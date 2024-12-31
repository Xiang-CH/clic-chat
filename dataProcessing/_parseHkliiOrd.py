#Adapted from: https://gist.github.com/kevinthwu/b656fd1b4c7f22b04fd979f9786ac8f1

from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
import json
import os
import re

opts = FirefoxOptions()
opts.add_argument("--headless")
DEBUG = False

driver = webdriver.Firefox(options=opts)

if not os.path.exists("ordinances"):
    os.mkdir("ordinances")

for lang in ['en', 'tc', 'sc']:
    for i in tqdm(range(1182), desc=f"Parsing ({lang})"): # replace 3 with 1183
        cap = i + 1
        
        # skip if already scraped
        if lang in os.listdir(f"ordinances") and f"cap_{cap}_{lang}.json" in os.listdir(f"ordinances/{lang}"):
            continue

        if DEBUG: print("========CAP: {}========".format(cap))
        
        # get the page
        url = f'https://hklii.hk/{lang}/legis/ord/{str(cap)}/full'
        driver.get(url)
        timeout = 3

        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'case-content'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")

        try:
        
            sections = driver.find_elements(By.TAG_NAME, "section")
            schedules = driver.find_elements(By.TAG_NAME, "schedule")
            cap_obj = {
                "cap_no": cap,
                "title": None,
                "url": url,
                "sections": [],
                "schedules": []
            }
            
            
            for sec in sections:
                if len(sec.text) < 5 or sec.get_attribute("temporalid") is None or sec.get_attribute("temporalid").startswith("sch"): # noise
                    continue 

                # get section name
                sec_name = sec.get_attribute("name")

                # get section number
                try:
                    sec_no = sec.find_element(By.TAG_NAME, "num").text[:-1].strip()
                except:
                    continue
                
                cap_obj["sections"].append({
                    "no": sec_no,
                    "heading": None,
                    "text": sec.text,
                    "url": url.replace("full", sec_name)
                })

                # get heading of the section
                try:
                    sec_heading = sec.find_element(By.TAG_NAME, "heading").text
                    # print("Heading: ", sec_heading)
                    cap_obj["sections"][-1]["heading"] = sec_heading

                    if DEBUG: print(sec_no, sec_heading)
                except:
                    if DEBUG: print(sec_no)
                    pass # no heading, probably repealed

                
                
                if sec_no == "1":
                    try:
                        title = re.search(r"This Ordinance may be cited as the (.+?)\.", "1. Short title\nThis Ordinance may be cited as the Interpretation and General Clauses Ordinance .").group().strip()
                        cap_obj["title"] = title if not title.endswith(".") else title[:-1].strip()
                    except:
                        pass


                # Some of the content would be uner <content> tag, and some would be under <def>, (maybe there will be more types of tags).
                # For simplicity, I print out everything in the section.
                # 
                #
                # You may also want to do sec.find_elements(By.TAG_NAME, "subsection") to get a list of subsections

            for sch in schedules:
                if len(sch.text) < 5:
                    continue

                sch_no = sch.find_element(By.TAG_NAME, "num").text.strip()
                sch_name = sch.get_attribute("name")

                cap_obj["schedules"].append({
                    "no": sch_no,
                    "heading": None,
                    "text": sch.text,
                    "url": url.replace("full", sch_name)
                })

                try:
                    sch_heading = sch.find_element(By.TAG_NAME, "heading").text
                    cap_obj["schedules"][-1]["heading"] = sch_heading
                    if DEBUG: print(sch_no, sch_heading)
                except:
                    pass


            if not os.path.exists(f"ordinances/{lang}"):
                os.mkdir(f"ordinances/{lang}")

            with open(f"ordinances/{lang}/cap_{cap}_{lang}.json", "w") as f:
                f.write(json.dumps(cap_obj, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Error in cap {cap}: {e}")
            with open(f"cap_{cap}_{lang}_{sec_name}.html", "w") as f:
                f.write(sec.get_attribute('innerHTML'))
            
            raise e
