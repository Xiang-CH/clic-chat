'''
This script parses the HKLII cases and saves them as csv files.
Author: Chen Xiang
Email: cxiang@connect.hku.hk
'''

import bs4
import json
import os
import re
import pandas as pd
import logging
from tqdm import tqdm
from docx import Document
from markdownify import markdownify as md
from concurrent.futures import ProcessPoolExecutor, as_completed

DEBUG = False
RAW_PATH = "raw_judgments"
BASE_PATH = "judgments2"

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', filename='parseHkliiCases.log', filemode='w')

def normalize_whitespace(text):
    # Replace all consecutive whitespace with a single space
    return re.sub(r'\s{2,}', ' ', text).strip()

def process_court_registry(lang, court_registry, position):
    court = court_registry.split("_")[0]
    registry_path = f"{RAW_PATH}/{lang}_registries/{court_registry}"

    # Read the pipe-delimited registry file
    df = pd.read_csv(registry_path, 
                    sep='|',
                    names=['empty','filename', 'date', 'case_name', 'citation', 'other_citations'],
                    encoding='utf-8')

    # Clean up the data by removing empty rows and stripping whitespace, and splitting the other_citations into case_number and law_report_citations
    df = df.dropna(subset=['filename', 'date', 'case_name', 'citation'])
    df["case_number"] = df["other_citations"].apply(lambda x: x.split(";")[-1] if pd.notna(x) else [])
    df["law_report_citations"] = df["other_citations"].apply(lambda x: x.split(";")[:-1] if pd.notna(x) else [])
    df = df.drop(columns=["other_citations", "empty"])

    case_data = []

    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc=f"Processing {court} cases ({lang})", position=position, leave=True):
        year, case_counter = row["filename"].split(".")[0].split("_")
        if int(year) < 2019:
            case_path = f"{RAW_PATH}/{lang}/pre_2019/{court}/data/{year}_{case_counter}.html"
        else:
            case_path = f"{RAW_PATH}/{lang}/{court}_{year}/{case_counter}.html"

        if not os.path.exists(case_path):
            logging.warning(f"Case path does not exist: {case_path}")
            continue

        # Parse the HTML file and extract the case information
        try:
            with open(case_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
        except Exception as e:
            logging.error(f"Error reading {case_path}: {e}")
            continue

        soup = bs4.BeautifulSoup(html_content, "html.parser")
        body = soup.find("form", {"name": "search_body"})
        if body is None: body = soup.find("body")

        # Ignore noise
        if not body or len(body.text.strip()) <= 300:
            logging.info(f"Ignoring {case_path} because it is noise")
            continue

        # Load docx if html redirects to docx
        if soup.find('script', string=lambda t: t and 'window.open' in t):
            docx_path = f"{RAW_PATH}/{lang}/{court}_{year}/{case_counter}.docx"
            if not os.path.exists(docx_path):
                logging.info(f"Docx file {docx_path} does not exist")
                continue

            doc = Document(docx_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"

            content = text

        else:
            content = md(str(body))


        year, post_citaiton_num = re.search(r"\[(\d+)]\s+\w+\s+(\d+)", row["citation"]).groups()
        case_data.append({
            "court": court,
            "registry": court_registry,
            "date": row["date"],
            "case_name": row["case_name"],
            "citation": row["citation"],
            "url": f"https://www.hklii.hk/en/cases/{court}/{year}/{post_citaiton_num}",
            "case_number": row["case_number"],
            "law_report_citations": row["law_report_citations"],
            "content": repr(content.strip())
        })

    return case_data

if not os.path.exists(BASE_PATH):
    os.mkdir(BASE_PATH)

def process_language(lang):
    court_registries = os.listdir(f"{RAW_PATH}/{lang}_registries")
    case_data = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_court_registry, lang, court_registry, 1+i) for i, court_registry in enumerate(court_registries)]
        for future in as_completed(futures):
            case_data.extend(future.result())
    return case_data

if __name__ == '__main__':
    for lang in ["eng", "chi"]:
        if os.path.exists(f"{BASE_PATH}/{lang}_cases.json"):
            continue
        print("\n\nProcessing", lang)
        case_data = process_language(lang)
        # Save the case data to JSON files or perform further processing as needed
        with open(f"{BASE_PATH}/{lang}_cases.json", "w", encoding="utf-8") as f:
            json.dump(case_data, f, ensure_ascii=False, indent=4)