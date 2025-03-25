import gradio as gr
import json
import os
from typing import Literal

import lancedb

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.chdir(os.path.dirname(os.path.abspath(__file__)))
db = lancedb.connect("db/lancedb")
ord_table = db.open_table("ordinances")
judg_table = db.open_table("judgements")

def search(query, table = "ordinances", top_k = 10, query_type: Literal["vector", "fts", "hybrid", "auto"] = "hybrid"):
    # table = db.open_table("judgements")
    if table == "ordinances":
        docs = ord_table.search(query, query_type=query_type, fts_columns="text").limit(top_k).to_list()
    elif table == "judgements":
        docs = judg_table.search(query, query_type=query_type, fts_columns="text").limit(top_k).to_list()
    else:
        docs = []

    return docs


# Search UI

with gr.Blocks() as search_block:
    with gr.Row():
        top_k = gr.Number(value=10, label="Top K")
        query_type = gr.Radio(["vector", "fts", "hybrid"], value="hybrid", label="Query Type")
    query = gr.Textbox(label="Query Input")
    search_btn = gr.Button("Search")

    with gr.Row():
        with gr.Column():
            ord = gr.Text(label="Ordinances Output")
            @gr.render(inputs=[query, top_k, query_type], triggers=[search_btn.click, query.submit])
            def render_ord_output(query, top_k, query_type):
                ords = search(query, "ordinances", top_k, query_type)

                for ord in ords:
                    gr.Markdown(f"**{ord['cap_title']}**\n\n{ord['text']}\n\n[Read More]({ord['url']})")
        with gr.Column():
            judgt = gr.Text(label="Judgements Output")
            @gr.render(inputs=[query, top_k, query_type], triggers=[search_btn.click, query.submit])
            def render_ord_output(query, top_k, query_type):
                judges = search(query, "judgements", top_k, query_type)

                for judge in judges:
                    gr.Markdown(f"**{judge['date']}: {judge['case_name']}**\n\n{judge['text']}\n\n[Read More]({judge['url']})")
    

    # search_btn.click(inputs=[query, top_k, query_type], outputs=[ord_output, judg_output], fn=search)

# Chat UI
from dotenv import load_dotenv
load_dotenv()

import time
# from openai import AzureOpenAI
# llm_client = AzureOpenAI(
#   azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
#   api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
#   api_version="2024-02-01"
# )

from openai import OpenAI
client = OpenAI(
    api_key = os.getenv("ZHIPUAI_API_KEY"),
    base_url = "https://open.bigmodel.cn/api/paas/v4/"
) 

sys_template = f"""You a Hong Kong legal questioning agent. You are required to answer questions from the public about the law in Hong Kong. You should provide accurate and reliable information to the public. **Do not answer** questions that are not related to the law in Hong Kong. You are not a lawyer and cannot offer legal advice. 

Answer the questions based on the informations given below. Always cite the source of your information and provide the url link, and never answer if the answer cannot be found in the information provided.

### Ordinances and Regulations
{{ordinances}}

### Judgements and Cases
{{judgements}}


- Answering Style: Be short and concise use Markdown to format your answers. Use callouts, bold, bullet points etc. to highlight important information.
- Citation Style: Always cite the source information by providing a hyperlink to the source url.
"""
session = gr

def get_sys_message(message, top_k, query_type):
    ordinances = search(message, "ordinances", top_k=top_k, query_type=query_type)
    ordinances = "\n".join([
        f"- **Cap {ord['cap_no']} ({ord['cap_title']}), {'Regulation' if ord['cap_no'][-1].isalpha() else 'Section'} {ord['section_no']} ({ord['section_heading']})**: {ord['text']}\n({ord['url']})"
        for ord in ordinances
    ])

    judgements = search(message, "judgements", top_k=top_k, query_type=query_type)
    judgements = "\n".join([f"- **{judge['date']}: {judge['case_name']} ({judge['court']})**: {judge['text']}\n({judge['url']})" for judge in judgements])

    sys_msg = sys_template.format(ordinances=ordinances, judgements=judgements)
    return sys_msg

def chat_reqponse(message, history, temperature, top_k, query_type):

    sys_msg = get_sys_message(message, top_k, query_type)
    messages = [{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": message}]

    response = client.chat.completions.create(
        # model="glm-4-flash",  
        model="glm-4-plus",
        messages=messages,
        temperature=temperature,
        stream=True
    ) 

    compeletion = ""
    for chunk in response:
        if len(chunk.choices) > 0:
            compeletion += chunk.choices[0].delta.content
            yield compeletion, sys_msg
    print(compeletion)
        


with gr.Blocks() as chat_block:
    sys_msg_block = gr.Markdown(label="System Message", render = False)
    with gr.Row():
        top_k = gr.Number(value=10, label="Top K")
        query_type = gr.Radio(["vector", "fts", "hybrid"], value="hybrid", label="Query Type", scale=2)
        temperature_slider = gr.Slider(minimum=0.1, maximum=1.0, step=0.1, value=0.9, label="Temperature", scale=2)
    with gr.Row():
        chat_interface = gr.ChatInterface(chat_reqponse, type="messages", save_history=True, additional_inputs=[temperature_slider, top_k, query_type], additional_outputs=[sys_msg_block])
    with gr.Row():
        sys_msg_block.render()


demo = gr.TabbedInterface(interface_list=[chat_block, search_block], tab_names=["Chat", "Search"], title="CLIC-Chat Demo")

if __name__ == "__main__":
    demo.launch(share=False)