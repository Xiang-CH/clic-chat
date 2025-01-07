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
OUTPUTDIR = "judgements_chunks"


if __name__ == "__main__":
    embedding_model = get_bge_m3_model()
    encoder = tiktoken.get_encoding(ENCODINGNAME)
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=ENCODINGNAME,
        chunk_size=MAXTOKEN,
        chunk_overlap=OVERLAP,
        separators=["\n", "\n\n", ". ", "? ", "! ", "; ", "。", "？", "！", "；"]
    )

    if not os.path.exists(OUTPUTDIR):
        os.mkdir(OUTPUTDIR)

    for lang in ["eng_cases", "chi_cases"]:

        if not os.path.exists(f"{OUTPUTDIR}/{lang}.csv"):
            df = pd.DataFrame(columns=["court", "date", "case_name", "citation", "case_number", "law_report_citations", "url","content", "vector"])
            df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False)

        with open(f"judgements/{lang}.json") as f:
            cases = json.load(f)

        chunks = []

        for case in tqdm(cases, leave=True, desc=f"Chunking cases {lang}"):

            tokens = encoder.encode(case["content"])

            # if less than max tokens, add to chunks
            if len(tokens) <= MAXTOKEN:
                chunks.append({
                    "court": case["court"],
                    "date": case["date"],
                    "case_name": case["case_name"],
                    "citation": case["citation"] + f"_{i}",
                    "case_number": case["case_number"],
                    "law_report_citations": case["law_report_citations"],
                    "url": case["url"],
                    "text": case["content"],
                    "vector": None
                })
            # break into chunks if more than max tokens
            else:
                texts = text_splitter.split_text(text=case["content"])
                for i, text in enumerate(texts):
                    chunks.append({
                        "court": case["court"],
                        "date": case["date"],
                        "case_name": case["case_name"],
                        "citation": case["citation"] + f"_{i}",
                        "case_number": case["case_number"],
                        "law_report_citations": case["law_report_citations"],
                        "url": case["url"],
                        "text": text,
                        "vector": None
                    })

                if len(chunks) >= 1000:
                    vectors = get_bge_m3_embeddings(embedding_model, [c["text"] for c in chunks]).tolist()
                    
                    df = pd.DataFrame(chunks)
                    df["vector"] = vectors
                    df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False, mode="a", header=False)
                    df = None
                    vectors = None
                    chunks = []

        if len(chunks) > 0:
            vectors = get_bge_m3_embeddings(embedding_model, [c["text"] for c in chunks]).tolist()
            
            df = pd.DataFrame(chunks)
            df["vector"] = vectors
            df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False, mode="a", header=False)


