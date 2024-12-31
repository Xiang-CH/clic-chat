
import bs4
import lxml
from tqdm import tqdm
import json
import os
import re
from markdownify import markdownify as md

DEBUG = False
BASE_PATH = "legislations"

def normalize_whitespace(text):
    # Replace all consecutive whitespace with a single space
    return re.sub(r'\s{2,}', ' ', text).strip()

if not os.path.exists(BASE_PATH):
    os.mkdir(BASE_PATH)

for lang in ['en', 'tc', 'sc']:
    files_names = [f for f in os.listdir(f"raw_legislations/{lang}") if not f.startswith(".")]

    for file_name in tqdm(sorted(files_names), desc=f"Parsing ({lang})"):
        cap = file_name.split("_")[1] # cap number

        # skip if already scraped
        if lang in os.listdir(BASE_PATH) and f"cap_{cap}_{lang}.json" in os.listdir(f"{BASE_PATH}/{lang}"):
            continue

        # Load the file
        file = f"raw_legislations/{lang}/{file_name}/" + [f for f in os.listdir(f"raw_legislations/{lang}/{file_name}") if f.endswith(".xml")][0]
        with open(file, "r") as f:
            soup = bs4.BeautifulSoup(f.read(), "xml")

        # Parse metadata
        meta = soup.find("meta")
        status = meta.find("docStatus").text # status of the cap
        if status != "In effect": # skip if repealed
            continue


        cap_type = "reg" if bool(re.search(r'[A-Za-z]', cap)) else "ord" # regulation or ordinance


        if DEBUG: print("========CAP: {}========".format(cap))
        
        # get the page
        url = f'https://hklii.hk/{lang}/legis/{cap_type}/{str(cap)}/full'
        try:
        
            cap_obj = {
                "cap_no": cap,
                "cap_type": cap_type,
                "interpretations": [],
                "title": normalize_whitespace(soup.find("docTitle").text).strip() if cap_type=="reg" else None,
                "url": url,
                "sections": [],
                "schedules": []
            }
            
            sections = soup.find_all("section")
            schedules = soup.find_all("schedule")

            if len(sections) == 0:
                paragraphs = [p for p in soup.find_all(["paragraph", "text"]) if not p.get("temporalId") or not p.get("temporalId").startswith("sch") ]
                
                content_tag = soup.new_tag("content")
                content_tag.string = " ".join([normalize_whitespace(p.get_text(separator=" ").strip()) for p in paragraphs]) 
                section_tag = soup.new_tag("section", attrs={"name": "full", "temporalId": "id"})
                num_tag = soup.new_tag("num", attrs={"value": "0"})
                section_tag.append(num_tag)
                section_tag.append(content_tag)
                sections = [section_tag]
                # print(section_tag)

            for sec in sections:
                sec_name = sec.get("name")
                if len(sec.text) < 5 or sec.get("temporalId") is None or sec.get("temporalId").startswith("sch") or (sec.get("reason") and sec.get("reason") != "inEffect"): # noise
                    continue 

                # get section number
                try:
                    sec_no = sec.find("num").get("value")
                    sec.find("num").replace_with("")
                except:
                    continue
                    
                # replace tables with markdown
                for table in sec.find_all("table"):
                    new_table = soup.new_tag("content")
                    new_table.string = md(table.prettify()).strip()
                    table.replace_with(new_table)

                # remove source note
                for note in sec.find_all("sourceNote"):
                    note.decompose()

                section_text = normalize_whitespace(sec.get_text(separator=" ").strip())
                interp_terms = [interp["term"] for interp in cap_obj["interpretations"] if interp["term"].lower() in section_text.lower()]
                
                cap_obj["sections"].append({
                    "no": sec_no,
                    "heading": None,
                    "text": section_text,
                    "url": url.replace("full", sec_name),
                    "interp_terms": interp_terms
                })

                # get heading of the section
                try:
                    sec_heading = normalize_whitespace(sec.find("heading").text)
                    cap_obj["sections"][-1]["heading"] = sec_heading

                    if DEBUG: print(sec_no, sec_heading)
                except:
                    if DEBUG: print(sec_no)
                    pass # no heading, probably repealed

                
                # get short title
                if cap_obj['title'] is None and sec.find("heading") and sec.find("heading").text == "Short title":
                    if (sec.find("shortTitle")):
                        cap_obj['title'] = normalize_whitespace(sec.find("shortTitle").text)
                    else:
                        try:
                            title = normalize_whitespace(re.search(r"This Ordinance may be cited as the (.+?)\.", sec.find("content").text).group().strip())
                            cap_obj["title"] = title if not title.endswith(".") else title[:-1].strip()
                        except:
                            pass

                # get interpretation
                if sec.find("heading") and sec.find("heading").text == "Interpretation":
                    for interp in sec.find_all("def"):
                        if interp.find("term") is None:
                            continue
                        cap_obj["interpretations"].append({
                            "term": normalize_whitespace(interp.find("term").text),
                            "text": normalize_whitespace(interp.text.strip())
                        })
                
            
            for sch in schedules:
                if len(sch.text) < 5 or sch.get("reason") != "inEffect":
                    continue

                sch_no = sch.find("num").get("value")
                sch_name = sch.get("name")

                for table in sch.find_all("table"):
                    new_table = soup.new_tag("content")
                    new_table.string = md(table.prettify()).strip()
                    table.replace_with(new_table)

                sch_text = normalize_whitespace(sch.get_text(separator=" ").strip())
                interp_terms = [interp["term"] for interp in cap_obj["interpretations"] if interp["term"].lower() in sch_text.lower()]

                cap_obj["schedules"].append({
                    "sch_no": sch_no,
                    "sch_name": sch_name,
                    "heading": None,
                    "text": sch_text,
                    "url": url.replace("full", sch_name),
                    "interp_terms": interp_terms
                })

                try:
                    sch_heading = sch.find("heading").text
                    cap_obj["schedules"][-1]["heading"] = normalize_whitespace(sch_heading)
                    if DEBUG: print(sch_no, sch_heading)
                except:
                    pass


            if not os.path.exists(f"{BASE_PATH}/{lang}"):
                os.mkdir(f"{BASE_PATH}/{lang}")

            with open(f"{BASE_PATH}/{lang}/cap_{cap}_{lang}.json", "w") as f:
                f.write(json.dumps(cap_obj, ensure_ascii=False, indent=2))
            
        except Exception as e:
            print(f"Error in cap {cap}: {e}")
            print("File:", file)
            with open(f"cap_{cap}_{lang}.xml", "w") as f:
                f.write(soup.prettify())
            
            raise e
    
