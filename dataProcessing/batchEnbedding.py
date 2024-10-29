import json
import os
import pandas as pd

# jsonl 格式 batch 请求文件
def to_batch_jsonl(file_in: str, file_out: str, model: str, url: str):
    if file_in.endswith('.csv'):
        df = pd.read_csv(file_in)
    elif file_in.endswith('.xlsx'):
        df = pd.read_excel(file_in)
    else:
        raise ValueError("Invalid file format")

    with open(file_out, 'w', encoding='utf-8') as f:
        for index, row in df.iterrows():
            
            data = get_batch_line(id=index, row=row, model=model, url=url)
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

            # if index == 10:
            #     break

# 获取单行 json 数据
def get_batch_line(id, row, model, url):
    data = {
        'custom_id': f"cap_{row['cap_no']}-section_{row['section_no']}",
        'method': 'POST',
        'url': url,
        'body': {
            'model': model,
            'input': row["text"],
        }
    }
  
    return data

if __name__ == "__main__":
    URL = "/v1/embeddings"
    MODEL = "embedding"

    for lang in ["sc", "tc"]:
        for file in os.listdir(f"ordinances/chunks/{lang}"):
            file_name_out = file.replace('.csv', '.jsonl')
            file_path_in = f"ordinances/chunks/{lang}/{file}"
            file_path_out = f"ordinances/batchReqs/{lang}/{file_name_out}"

            if not os.path.exists(f"ordinances/batchReqs/{lang}"):
                os.mkdir(f"ordinances/batchReqs/{lang}")
            if os.path.exists(file_path_out):
                continue
            
            to_batch_jsonl(file_path_in, file_path_out, MODEL, URL)
            break
