import os
import json
import tiktoken
import pandas as pd
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bge_m3 import get_bge_m3_model, get_bge_m3_embeddings
import multiprocessing as mp
from filelock import FileLock
import torch

ENCODINGNAME = "o200k_base"
MAXTOKEN = 512
OVERLAP = 128
OUTPUTDIR = "judgements_chunks"
LANGS = ["eng_cases", "chi_cases"]

def process_cases(cases, lang, gpu_id):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    embedding_model = get_bge_m3_model()
    encoder = tiktoken.get_encoding(ENCODINGNAME)
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=ENCODINGNAME,
        chunk_size=MAXTOKEN,
        chunk_overlap=OVERLAP,
        separators=["\n", "\n\n", ". ", "? ", "! ", "; ", "。", "？", "！", "；"]
    )

    processesed = pd.read_csv(f"{OUTPUTDIR}/{lang}.csv")["url"].tolist()

    chunks = []

    for case in tqdm(cases, leave=True, desc=f"({gpu_id}) Chunking cases {lang}", position=gpu_id):

        if case["url"] in processesed:
            continue

        tokens = encoder.encode(case["content"])

        # if less than max tokens, add to chunks
        if len(tokens) <= MAXTOKEN:
            chunks.append({
                "court": case["court"],
                "date": case["date"],
                "case_name": case["case_name"],
                "citation": case["citation"],
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

            if len(chunks) >= 500:
                vectors = get_bge_m3_embeddings(embedding_model, [c["text"] for c in chunks]).tolist()
                
                df = pd.DataFrame(chunks)
                df["vector"] = vectors
                with FileLock(f"{OUTPUTDIR}/{lang}.csv.lock"):
                    df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False, mode="a", header=False)
                
                # Clear GPU memory
                del df
                del vectors
                del chunks[:]
                torch.cuda.empty_cache()

    if len(chunks) > 0:
        vectors = get_bge_m3_embeddings(embedding_model, [c["text"] for c in chunks]).tolist()
        
        df = pd.DataFrame(chunks)
        df["vector"] = vectors
        with FileLock(f"{OUTPUTDIR}/{lang}.csv.lock"):
            df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False, mode="a", header=False)

def process_language(lang, gpus):
    if not os.path.exists(OUTPUTDIR):
        os.mkdir(OUTPUTDIR)

    if not os.path.exists(f"{OUTPUTDIR}/{lang}.csv"):
        df = pd.DataFrame(columns=["court", "date", "case_name", "citation", "case_number", "law_report_citations", "url", "content", "vector"])
        df.to_csv(f"{OUTPUTDIR}/{lang}.csv", index=False)

    with open(f"judgements/{lang}.json") as f:
        cases = json.load(f)

    num_cases = len(cases)
    chunk_size = num_cases // gpus

    processes = []
    for i in range(gpus):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size if i < gpus - 1 else num_cases
        p = mp.Process(target=process_cases, args=(cases[start_idx:end_idx], lang, i))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

if __name__ == "__main__":
    for lang in LANGS:
        process_language(lang, torch.cuda.device_count()) 