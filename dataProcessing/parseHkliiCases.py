'''
Adapted from: https://gist.github.com/kevinthwu/b656fd1b4c7f22b04fd979f9786ac8f1

This script parses the HKLII cases and saves them as JSON files.
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

DEBUG = False
RAW_PATH = "raw_judgments"
BASE_PATH = "judgments"

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s', filename='parseHkliiCases.log', filemode='w')

def normalize_whitespace(text):
    # Replace all consecutive whitespace with a single space
    return re.sub(r'\s{2,}', ' ', text).strip()

if not os.path.exists(BASE_PATH):
    os.mkdir(BASE_PATH)

for lang in tqdm(["eng", "chi"], desc="Processing languages", leave=True):
    court_registries = os.listdir(f"{RAW_PATH}/{lang}_registries")
    case_data = []

    for court_registry in tqdm(court_registries, desc=f"Processing {lang} court registries", leave=True):
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

        for index, row in tqdm(df.iterrows(), total=df.shape[0], desc=f"Processing {court} cases ({lang})", leave=False):
            year, case_counter = row["filename"].split(".")[0].split("_")
            if int(year) < 2019:
                case_path = f"{RAW_PATH}/{lang}/pre_2019/{court}/data/{year}_{case_counter}.html"
            else:
                case_path = f"{RAW_PATH}/{lang}/{court}_{year}/{case_counter}.html"

            if not os.path.exists(case_path):
                continue

            # Parse the HTML file and extract the case information
            try:
                with open(case_path, "r", encoding="utf-8", errors="ignore") as f:
                    html_content = f.read()
            except Exception as e:
                logging.warning(f"Error reading {case_path}: {e}")
                exit()

            soup = bs4.BeautifulSoup(html_content, "html.parser")
            body = soup.find("form", {"name": "search_body"})
            if body is None: body = soup.find("body")

            # Ignore noise
            if len(body.text.strip()) <= 300:
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

            case_data.append({
                "court": court,
                "registry": court_registry,
                "date": row["date"],
                "case_name": row["case_name"],
                "citation": row["citation"],
                "case_number": row["case_number"],
                "law_report_citations": row["law_report_citations"],
                "content": content
            })

    df = pd.DataFrame(case_data)
    df.to_csv(f"{BASE_PATH}/{lang}_cases.csv", index=False)



