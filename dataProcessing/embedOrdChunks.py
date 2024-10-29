import os
import pandas as pd
import tiktoken
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()
embedding_function = AzureOpenAIEmbeddings(model="embedding")

for lang in tqdm(["en", "sc", "tc"], desc="Lang"):
    files = os.listdir(f"ordinances/chunks/{lang}")

    if not os.path.exists(f"ordinances/embeddedChunks/{lang}"):
        os.mkdir(f"ordinances/embeddedChunks/{lang}")
    embedded_files = os.listdir(f"ordinances/embeddedChunks/{lang}")

    for file in tqdm(files, leave=False, desc=f"Embedding Caps ({lang})"):
        if file in embedded_files:
            continue
        # print("Embedding", file)
        df = pd.read_csv(f"ordinances/chunks/{lang}/{file}")
        texts = df["text"].tolist()

        vectors = []
        for text in tqdm(texts, leave=False, desc="Embedding Chunks"):
            vector = embedding_function.embed_documents([text])
            vectors.append(vector[0])

        # vectors = embedding_function.embed_documents(texts)
        df["vector"] = vectors

        # save embeddings
        df.to_csv(f"ordinances/embeddedChunks/{lang}/{file}", index=False)
    

