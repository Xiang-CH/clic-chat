import requests
import json
import pandas

# URL = "http://localhost:8000/api/chat"
URL = "https://clic.cxiang.site/api/chat"

def make_request(msg):

    response = requests.post(URL, 
        json={
            "id": "test",
            "messages": [
                {
                    "role": "user",
                    "content": msg
                }
            ]
        },
        stream=True
    )

    # Process the streaming response
    full_response = ""
    for line in response.iter_lines():
        if line:
            # Decode the line
            decoded_line = line.decode('utf-8')
            
            # Parse the data based on the protocol format (x-vercel-ai-data-stream)
            if decoded_line.startswith('0:'):  # Text content
                content = json.loads(decoded_line[2:])
                full_response += content
            elif decoded_line.startswith('d:'):  # Done
                done_data = json.loads(decoded_line[2:])
                # print(f"Done: {done_data}")

    return full_response

def text_contains_cap(text, cap_no):
    return f"Cap. {cap_no}" in text or f"Cap {cap_no}" in text or f"Cap.{cap_no}" in text or f"cap. {cap_no}" in text or f"cap {cap_no}" in text or f"cap.{cap_no}" in text or f"ord/{cap_no}" in text or f"reg/{cap_no}" in text

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
    df.to_json("eval/cap_qa_pairs_clic.json", orient="records", indent=2, force_ascii=False)
