import gradio as gr
import os
from typing import Literal
from demo.prompts import getQAPrompt, getTasksPrompt, getQueryRewritePrompt, consultTaskSchema

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
        docs = judg_table.search(query, query_type=query_type, fts_columns="case_summary").limit(top_k).to_list()
    else:
        docs = []

    return docs


# Search UI

with gr.Blocks() as search_block:
    with gr.Row():
        top_k = gr.Number(value=6, label="Top K")
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
                    gr.Markdown(f"**{ord['cap_title']}**\n\n{ord['text']}\n\n[Read More]({ord['url']})\n\nScore: {ord['_relevance_score']}")
        with gr.Column():
            judgt = gr.Text(label="Judgements Output")
            @gr.render(inputs=[query, top_k, query_type], triggers=[search_btn.click, query.submit])
            def render_ord_output(query, top_k, query_type):
                judges = search(query, "judgements", top_k, query_type)

                for judge in judges:
                    gr.Markdown(f"**{judge['date']}: {judge['case_name']}**\n\n{judge['case_summary']}\n\n[Read More]({judge['url']})\n\nScore: {judge['_relevance_score']}")
    

    # search_btn.click(inputs=[query, top_k, query_type], outputs=[ord_output, judg_output], fn=search)

# Chat UI
from dotenv import load_dotenv
load_dotenv(override=True)


from openai import AzureOpenAI
llm_client = AzureOpenAI(
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2025-03-01-preview"
)
# model="glm-4-flash",
MODEL="gpt-4o-mini"
# model="glm-4-plus",

# from openai import OpenAI
# llm_client = OpenAI(
#     api_key = os.getenv("ZHIPUAI_API_KEY"),
#     base_url = "https://open.bigmodel.cn/api/paas/v4/"
# ) 



def get_search_query(message, history):
    conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history]) if history else "No conversation history."

    user_message = "### Conversation History\n" + conversation + "\n\n### New User Message\n" + message

    complete_message = llm_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": getQueryRewritePrompt()}] + [{"role": "user", "content": user_message}],
    )
    print("search complete")
    return complete_message.choices[0].message.content

def format_ordinance(ordinances):
    return "\n\n".join([
        f"- **Cap {ord['cap_no']} ({ord['cap_title']}), {'Regulation' if ord['cap_no'][-1].isalpha() else 'Section'} {ord['section_no']} ({ord['section_heading']})**: {ord['text']}\n({ord['url']})"
        for ord in ordinances
    ])

def format_judgement(judgements):
    return "\n\n".join([f"""- **{judge['date']}: {judge['case_name']} ({judge['court']})**: {judge['case_summary']}\n->Case Causes: {judge['case_causes']}\n->Court Decision: {judge['court_decision']}\n({judge['url']})""" for judge in judgements])

def get_sys_message(message, top_k, query_type):
    ordinances = search(message, "ordinances", top_k=top_k, query_type=query_type)
    ordinances = format_ordinance(ordinances)

    judgements = search(message, "judgements", top_k=top_k, query_type=query_type)
    judgements = format_judgement(judgements)

    sys_msg = getQAPrompt().format(ordinances=ordinances, judgements=judgements)
    return sys_msg

def chat_reqponse(message, history, temperature, top_k, query_type):
    search_query = get_search_query(message, history)
    sys_msg = get_sys_message(search_query, top_k, query_type)
    messages = [{"role": "system", "content": sys_msg}] + history + [{"role": "user", "content": message}]

    metadata_display = f"### Search Query\n{search_query}\n\n### System Message\n{sys_msg}"

    response = llm_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        stream=True
    ) 

    compeletion = ""
    for chunk in response:
        if len(chunk.choices) > 0:
            if chunk.choices[0].delta.content:
                compeletion += chunk.choices[0].delta.content
                yield compeletion, metadata_display
        

with gr.Blocks(fill_height=True, elem_id="chat_block") as chat_block:
    sys_msg_block = gr.Markdown(label="System Message", render = False)
    with gr.Row():
        top_k = gr.Number(value=6, label="Top K")
        query_type = gr.Radio(["vector", "fts", "hybrid"], value="vector", label="Search Method", scale=2)
        temperature_slider = gr.Slider(minimum=0.1, maximum=1.0, step=0.1, value=0.2, label="Temperature", scale=2)
    with gr.Row(height=800):
        chat_interface = gr.ChatInterface(chat_reqponse, type="messages", save_history=True, additional_inputs=[temperature_slider, top_k, query_type], additional_outputs=[sys_msg_block], fill_height=True)
    with gr.Row():
        sys_msg_block.render()



# Consult UI

def get_tasks(consult_topic, search_query, top_k, query_type):
    ordinances = search(search_query, "ordinances", top_k=top_k, query_type=query_type)
    ordinances = format_ordinance(ordinances)

    judgements = search(search_query, "judgements", top_k=top_k, query_type=query_type)
    judgements = format_judgement(judgements)

    tasks_prompt = getTasksPrompt().format(ordinances=ordinances, judgements=judgements)

    tasks_list = llm_client.beta.chat.completions.parse(
        model=MODEL,
        messages=[{"role": "system", "content": tasks_prompt}, {"role": "user", "content": f"## Consultation Topic\n{consult_topic}"}],
        response_format = consultTaskSchema
    )

    return tasks_list.choices[0].message.parsed

def consult_response(message, history, temperature, top_k, query_type):
    search_query = get_search_query(message, history)
    tasks = get_tasks(message, search_query, top_k, query_type)
    
    # Format tasks into a markdown string
    tasks_markdown = tasks.model_dump_json(indent=2)
    
    return tasks_markdown, "### Search Query\n" + search_query

# Update the layout to show tasks in chat
with gr.Blocks(fill_height=True, elem_id="consult_block") as consult_block:
    sys_msg_block = gr.Markdown(label="System Message", render = False)
    with gr.Row():
        top_k = gr.Number(value=6, label="Top K")
        query_type = gr.Radio(["vector", "fts", "hybrid"], value="vector", label="Search Method", scale=2)
        temperature_slider = gr.Slider(minimum=0.1, maximum=1.0, step=0.1, value=0.2, label="Temperature", scale=2)
    with gr.Row():
        chat_interface = gr.ChatInterface(
            consult_response,
            type="messages",
            additional_inputs=[temperature_slider, top_k, query_type],
            additional_outputs=[sys_msg_block],
            fill_height=True
        )
    with gr.Row():
        sys_msg_block.render()


demo = gr.TabbedInterface(interface_list=[consult_block, chat_block, search_block], tab_names=["Consult", "Chat", "Search"], title="CLIC-Chat Demo")

if __name__ == "__main__":
    demo.launch(share=False)