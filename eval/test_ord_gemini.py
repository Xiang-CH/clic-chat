from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

from dotenv import load_dotenv

import pandas
import os
import time

load_dotenv(".env", override=True)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

google_search_tool = Tool(
    google_search = GoogleSearch()
)

def make_request(msg):
    response = client.models.generate_content(
        contents=[msg],
        model="gemini-2.0-flash",
        config=GenerateContentConfig(tools=[google_search_tool], system_instruction="You are a Hong Kong legal assistant."),
    )

    return response.text

def text_contains_cap(text, cap_no):
    return f"Cap. {cap_no}" in text or f"Cap {cap_no}" in text or f"Cap.{cap_no}" in text or f"cap. {cap_no}" in text or f"cap {cap_no}" in text or f"cap.{cap_no}" in text or f"ord/{cap_no}" in text or f"reg/{cap_no}" in text

if __name__ == "__main__":
    if os.path.exists("eval/cap_qa_pairs_gemini.json"):
        df = pandas.read_json("eval/cap_qa_pairs_gemini.json")
    else:
        df = pandas.read_json("eval/cap_qa_pairs_.json")
    total_cited = 0

    print(df.head(2))

    try:
        for index, row in df.iterrows():

            if df.at[index, "tool_response"] is not None:
                continue

            df.at[index, "index"] = index
            msg = row["Question"]
            cap_nos = [ordinance["cap_no"] for ordinance in row["ordinances"]]
            ans = make_request(msg)
            df.at[index, "tool_response"] = ans
            contains_cap = any(text_contains_cap(ans, cap_no) for cap_no in cap_nos)
            df.at[index, "contains_cap"] = contains_cap
            total_cited += int(contains_cap)
            print(f"Question: {index + 1} | Contains cap: {contains_cap}")
            time.sleep(4)

        print(f"Total cited: {total_cited}")
        df.to_json("eval/cap_qa_pairs_gemini.json", orient="records", indent=2, force_ascii=False)
    except Exception as e:
        print(e)
        df.to_json("eval/cap_qa_pairs_gemini.json", orient="records", indent=2, force_ascii=False)
