import os
import json
import tiktoken
import pandas as pd
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bge_m3 import get_bge_m3_model, get_bge_m3_embeddings


ENCODINGNAME = "o200k_base"
MAXTOKEN = 512
OVERLAP = 128
OUTPUTDIR = "legislations_chunks"


if __name__ == "__main__":
    embedding_model = get_bge_m3_model()
    encoder = tiktoken.get_encoding(ENCODINGNAME)
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=ENCODINGNAME,
        chunk_size=MAXTOKEN,
        chunk_overlap=OVERLAP,
        separators=["\n", "\n\n", ". ", "? ", "! ", "; ", "。", "？", "！", "；"]
    )

    short_title = {
        "en": "Short title",
        "sc": "简称",
        "tc": "簡稱"
    }

    if not os.path.exists(OUTPUTDIR):
        os.mkdir(OUTPUTDIR)

    for lang in ["en"]:

        if not os.path.exists(f"legislations/{lang}.csv"):
            df = pd.DataFrame(columns=["cap_no", "cap_title", "section_no", "section_heading", "text", "url", "type", "vector"])
            df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False)

        files = os.listdir(f"legislations/{lang}")
        for file in tqdm(files, leave=False, desc="Chunking Caps"):

            chunks = []

            with open(f"legislations/{lang}/{file}") as f:
                data = json.load(f)

            # skip if no sections
            if len(data["sections"]) == 0:
                continue

            cap_title = data["title"]

            # chunk the sections
            for sec in tqdm(data["sections"], leave=False, desc=f"Chunking Sections"):
                if not sec["heading"] or "Interpretation" in sec["heading"]:
                    continue

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

            vectors = get_bge_m3_embeddings(embedding_model, [c["text"] for c in chunks]).tolist()
            
            # save chunks
            if len(chunks) > 0:
                df = pd.DataFrame(chunks)
                df["vector"] = vectors
                print(df)
                df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False, mode="a", header=False)
                df = None
                vectors = None


