# %%
import pandas as pd
from filelock import FileLock
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from llm_client import generate_extra_meta

num_gpus = 4

# %%
os.chdir(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_json("../../judgements/eng_cases.json")
df.info()

# %%
# Count entries for each court
court_counts = df['court'].value_counts()

# Display the counts
print("Number of cases by court:")
print(court_counts)

# Add this function to handle processing for each GPU
def process_chunk(cases, gpu_id, output_file):
    # Set environment variable to control which GPU this process uses
    # os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    results = []
    tmp_file = f"{output_file}_gpu{gpu_id}_tmp.json"
    tmp_lock = FileLock(f"{tmp_file}.lock")
    
    # Load existing temp results if available
    if os.path.exists(tmp_file):
        try:
            with open(tmp_file, "r") as f:
                results = json.load(f)
            
            # Get URLs of already processed cases
            processed_urls = {item["url"] for item in results}
            
            # Filter out already processed cases
            cases = [case for case in cases if case["url"] not in processed_urls]
            print(f"GPU {gpu_id}: Loaded {len(results)} existing results. {len(cases)} cases remaining.")
        except json.JSONDecodeError:
            print(f"GPU {gpu_id}: Error loading temp file, starting fresh")
            results = []
    
    for case in tqdm(cases, desc=f"GPU {gpu_id} processing", position=gpu_id+1):
        try:
            data = generate_extra_meta(case["content"], gpu_id)  # Use 0 since each process has its own GPU
            result_item = {
                **data.model_dump(),
                "case_name": case["case_name"],
                "court": case["court"],
                "date": case["date"].strftime("%Y-%m-%d") if hasattr(case["date"], "strftime") else case["date"],
                "citation": case["citation"],
                "case_number": case["case_number"],
                "law_report_citations": case["law_report_citations"],
                "url": case["url"]
            }
            results.append(result_item)
            
            # Save intermediate results after each case
            with tmp_lock:
                with open(tmp_file, "w") as f:
                    f.write(json.dumps(results, indent=2))
                    
        except Exception as e:
            print(f"Error processing case on GPU {gpu_id}: {str(e)}")
            print(f"Case URL: {case['url']}")
    
    return results


def process_cases(df, output_file="cases_meta"):
    cases = df.to_dict(orient='records')
    results = []
    
    # Load existing partial results if available
    if os.path.exists(f"{output_file}_partial.json"):
        with open(f"{output_file}_partial.json", "r") as f:
            results = json.load(f)
        
        # Get URLs of already processed cases
        processed_urls = {item["url"] for item in results}
        
        # Filter out already processed cases
        cases = [case for case in cases if case["url"] not in processed_urls]
        print(f"Loaded {len(results)} existing results. {len(cases)} cases remaining to process.")

    lock = FileLock(f"{output_file}_partial.json.lock")

    # Split cases into chunks for each GPU
    num_cases = len(cases)
    chunk_size = (num_cases + num_gpus - 1) // num_gpus  # Ceiling division
    case_chunks = [cases[i:i + chunk_size] for i in range(0, num_cases, chunk_size)]
    print(f"Split cases into {len(case_chunks)} chunks for each GPU")

    # Process cases in parallel using ProcessPoolExecutor
    all_results = []
    print(f"Creating ProcessPoolExecutor with {num_gpus} workers")
    with ProcessPoolExecutor(max_workers=num_gpus) as executor:
        futures = [executor.submit(process_chunk, chunk, gpu_id, output_file) for gpu_id, chunk in enumerate(case_chunks)]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Collecting results"):
            try:
                chunk_results = future.result()
                all_results.extend(chunk_results)
                
                # Save intermediate results after each chunk completes after 
                with lock:
                    with open(f"{output_file}_partial.json", "w") as f:
                        f.write(json.dumps(all_results, indent=2))
            except Exception as e:
                print(f"Error processing chunk: {str(e)}")

    # Combine all results
    results = all_results

    with open(f"{output_file}.json", "w") as f:
        f.write(json.dumps(results, indent=2))

# %%
process_cases(df)


