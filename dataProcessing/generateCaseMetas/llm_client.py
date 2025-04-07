import os
import time
from dotenv import load_dotenv
from openai import OpenAI
# from ollama import chat, Client 
from schema import CaseMeta
import random

load_dotenv(dotenv_path=".env", override=True)

# client = OpenAI(
#     api_key = os.getenv("ZHIPUAI_API_KEY"),
#     base_url = "https://open.bigmodel.cn/api/paas/v4/"
# ) 
# print(os.getenv("AZURE_OPENAI_ENDPOINT"))
# client = AzureOpenAI(
#   azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
#   api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
#   api_version=os.getenv("OPENAI_API_VERSION")
# )
# os.environ["OLLAMA_MAX_LOADED_MODELS"] = "4"
# os.environ["OLLAMA_NUM_PARALLEL"] = "4"

# llm = OpenAI(
#     api_key = "ollama",
#     base_url = "http://localhost:11434/v1"
# )

llms = [
    OpenAI(
        api_key = "ollama",
        base_url = "http://localhost:11434/v1"
    ),
    OpenAI(
        api_key = "ollama",
        base_url = "http://localhost:11435/v1"
    ),
    OpenAI(
        api_key = "ollama",
        base_url = "http://localhost:11436/v1"
    ),
    OpenAI(
        api_key = "ollama",
        base_url = "http://localhost:11437/v1"
    ),
]


os.chdir(os.path.dirname(os.path.abspath(__file__)))

def generate_extra_meta(text, gpu_id=0) -> CaseMeta :
    # client.chat.completions.create
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # response = chat(
            #     # model="qwen2.5",
            #     model="myaniu/qwen2.5-1m:7b-instruct-q8_0",
            #     messages=[
            #         {"role": "system", "content": "You are a Hong Kong Legal Case Meta Data Extractor. Please provide comprehensive information about the case for each of the fields. Only extract the information from the case. Do not make up any information. No need to mention the court name in the summary, the summary should cover all aspect of the case in around 500 words.\n\nIdentify all the legislations (ordinance / regulation) refered in the case."},
            #         {"role": "user", "content": f"{text}"}
            #     ],
            #     options={
            #         "temperature": 0.01,
            #         # "num_ctx": 131050,
            #         "num_ctx": 150000,
            #         # "max_tokens": 131000
            #     },
            #     keep_alive="5s",
            #     format=CaseMeta.model_json_schema()
            # )
            
            # output = CaseMeta.model_validate_json(response.message.content)
            response = llms[gpu_id].beta.chat.completions.parse(
                # model="qwen2.5",
                model="myaniu/qwen2.5-1m:7b-instruct-q8_0",
                messages=[
                    {"role": "system", "content": "You are a Hong Kong Legal Case Meta Data Extractor. Please provide comprehensive information about the case for each of the fields. Only extract the information from the case. Do not make up any information. No need to mention the court name in the summary, the summary should cover all aspect of the case in around 500 words.\n\nIdentify all the legislations (ordinance / regulation) refered in the case."},
                    {"role": "user", "content": f"{text}"}
                ],
                temperature=0.01,
                max_tokens=150000,
                timeout=180,
                response_format=CaseMeta
            )
            
            output = response.choices[0].message.parsed
            return output
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt+1} failed with error: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay + random.uniform(0, 1))  # Add jitter to avoid thundering herd
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"All {max_retries} attempts failed for text: {text[:100]}...")
                raise

if __name__ == "__main__":
    import pandas as pd
    import json
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm
    num_gpus = 4

    df = pd.read_json("../../judgements/eng_cases.json")
    print(df.info())

    # Select a few random cases
    sample_size = 12
    random_indices = random.sample(range(len(df)), sample_size)
    texts = [df["content"][i] for i in random_indices]

    results = []

    # Split cases into chunks for each GPU
    num_cases = len(texts)
    chunk_size = (num_cases + num_gpus - 1) // num_gpus  # Ceiling division
    case_chunks = [texts[i:i + chunk_size] for i in range(0, num_cases, chunk_size)]

     # Process cases in parallel using ThreadPoolExecutor instead of ProcessPoolExecutor
    print(f"Creating ThreadPoolExecutor with {num_gpus} workers")
    with ThreadPoolExecutor(max_workers=num_gpus) as executor:
        # futures = [executor.submit(generate_extra_meta, text) for text in texts]

        futures_with_gpu = []
        
        for gpu_id, case_chunk in enumerate(case_chunks):
            for case in case_chunk:
                # Pass GPU ID with each case
                futures_with_gpu.append((
                    executor.submit(generate_extra_meta, case, gpu_id),
                    case,
                    gpu_id
                ))
        
        # for future, text in tqdm(zip(as_completed(futures), texts), total=len(texts), desc="Processing cases"):
        for (future, text, gpu_id) in tqdm(futures_with_gpu, total=len(futures_with_gpu), desc="Processing cases"):
            try:
                data = future.result()
                results.append({"data": data.model_dump(), "text": text})
                
                # Save intermediate results after each successful completion
                with open("results_partial.json", "w") as f:
                    f.write(json.dumps(results, indent=2))
            except Exception as e:
                print(f"Error processing case: {str(e)}")

    with open("results.json", "w") as f:
        f.write(json.dumps(results, indent=2))

