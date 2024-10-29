import os
import re
import json
import tiktoken
import pandas as pd
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter

ENCODINGNAME = "o200k_base"
MAXTOKEN = 512
OVERLAP = 128
encoder = tiktoken.get_encoding(ENCODINGNAME)
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name=ENCODINGNAME,
    chunk_size=MAXTOKEN,
    chunk_overlap=OVERLAP,
    separators=["\n", "\n\n", ". ", "? ", "! ", "; ", "。", "？", "！", "；"]
)

title_regex = {
    "en": r"as the (.+? Ordinance)",
    "sc": r"(《[^》]+》)",
    "tc": r"(《[^》]+》)"
}

short_title = {
    "en": "Short title",
    "sc": "简称",
    "tc": "簡稱"
}

for lang in tqdm(["en", "sc", "tc"], desc="Lang"):
    files = os.listdir(f"ordinances/full_cap/{lang}")
    for file in tqdm(files, leave=False, desc="Chunking Caps"):

        chunks = []

        with open(f"ordinances/full_cap/{lang}/{file}") as f:
            data = json.load(f)

        # skip if no sections
        if len(data["sections"]) == 0:
            continue

        cap_title = data["title"].split("cited as the", maxsplit=1)[1].strip()

        # chunk the sections
        for sec in tqdm(data["sections"], leave=False, desc=f"Chunking Sections"):
            if not sec["heading"] or short_title[lang] in sec["heading"]:
                match = re.search(title_regex[lang], sec["text"])
                if match:
                    cap_title = match.group(1)
                    continue
                else:
                    break

            tokens = encoder.encode(sec["text"])

            # if less than max tokens, add to chunks
            if len(tokens) <= MAXTOKEN:
                chunks.append({
                    "cap_no": data["cap_no"],
                    "cap_title": cap_title,
                    "section_no": sec["no"],
                    "section_heading": sec["heading"],
                    "text": sec["text"],
                    "url": sec["url"],
                    "type": "cap",
                    "vector": None
                })
            # break into chunks if more than max tokens
            else:
                texts = text_splitter.split_text(sec["text"])
                for i, text in enumerate(texts):
                    chunks.append({
                        "cap_no": data["cap_no"],
                        "cap_title": cap_title,
                        "section_no": sec["no"] + f"_{i}",
                        "section_heading": sec["heading"],
                        "text": text,
                        "url": sec["url"],
                        "type": "cap",
                        "vector": None
                    })
        
        # save chunks
        if not os.path.exists(f"ordinances/chunks/{lang}"):
            os.mkdir(f"ordinances/chunks/{lang}")
        if len(chunks) > 0:
            df = pd.DataFrame(chunks)
            df.to_csv(f"ordinances/chunks/{lang}/cap_{data["cap_no"]}_{lang}.csv", index=False)


