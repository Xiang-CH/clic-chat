import requests
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import pandas
import os

load_dotenv(".env", override=True)

client = AzureOpenAI(
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

def make_request(msg):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a Hong Kong legal assistant."
            },
            {
                "role": "user",
                "content": msg
            }
        ],
        model="gpt-4o-mini",
    )

    return response.choices[0].message.content

def text_contains_cap(text, cap_no):
    return f"Cap. {cap_no}" in text or f"Cap {cap_no}" in text or f"Cap.{cap_no}" in text or f"cap. {cap_no}" in text or f"cap {cap_no}" in text or f"cap.{cap_no}" in text or f"ord/{cap_no}" in text or f"reg/{cap_no.lower()}" in text

if __name__ == "__main__":
    df = pandas.read_json("eval/cap_qa_pairs_.json")
    total_cited = 0

    print(df.head(2))

    for index, row in df.iterrows():
        df.at[index, "index"] = index
        msg = row["Question"]
        cap_nos = [ordinance["cap_no"] for ordinance in row["ordinances"]]
        ans = make_request(msg)
        df.at[index, "tool_response"] = ans
        contains_cap = any(text_contains_cap(ans, cap_no) for cap_no in cap_nos)
        df.at[index, "contains_cap"] = contains_cap
        total_cited += int(contains_cap)
        print(f"Question: {index + 1} | Contains cap: {contains_cap}")

    print(f"Total cited: {total_cited}")
    df.to_json("eval/cap_qa_pairs_gpt4omini.json", orient="records", indent=2, force_ascii=False)
