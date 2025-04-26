import os
import json
import lancedb
import time

import re
from sentence_transformers import SentenceTransformer
from typing import List, Literal
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AzureOpenAI
from .utils.prompt import ClientMessage, convert_to_openai_messages
from .utils.tools import search_ordinance_or_regulation_tool, search_cases_tool

from .helper import get_search_query, process_stream_chunks, query_expand, get_tasks
from .utils.prompts import getQAPrompt, getAskClarificationPrompt, getDoTaskPrompt


# load_dotenv(".env.local")
load_dotenv()

kv = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MODEL = "gpt-4o-mini"
client = AzureOpenAI(
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version="2025-03-01-preview"
)

db = lancedb.connect(os.environ.get("DB_PATH"))
model = None
ord_table = db.open_table("ordinances")
judg_table = db.open_table("judgements")


def search(queries: str | List[str], table = "both", top_k = 10, query_type: Literal["vector", "fts", "hybrid", "auto"] = "vector"):
    start_time = time.time()
    global model
    if model is None:
        model = SentenceTransformer('BAAI/bge-m3', device="cuda")
    
    if isinstance(queries, str):
        queries = [queries]

    ord_docs = []
    case_docs = []
    
    if table == "ordinances" or table == "both":
        for query in queries:
            results = ord_table.search(query, query_type=query_type, fts_columns="text").limit(top_k).select(
                ["cap_no", "section_no", "type", "cap_title", "section_heading", "text", "url"]
            ).to_list()
            for doc in results:
                if doc not in ord_docs:
                    ord_docs.append(doc)
        print("get ords time:", time.time() - start_time, flush=True)

    if table == "judgements" or table == "both":
        for query in queries:
            results = judg_table.search(query, query_type=query_type, fts_columns="case_summary").select(
                ["crime_name", "case_type", "court", "case_name","case_summary","date","case_number", "case_causes", "court_decision", "url"]
            ).limit(top_k).to_list()
            for doc in results:
                if doc not in case_docs:
                    case_docs.append(doc)
        for doc in case_docs:
            doc["date"] = doc["date"].strftime("%Y-%m-%d")
        print("get cases time:", time.time() - start_time, flush=True)
    
    docs = {}
    if table == "both":
        docs = {"ordinances": ord_docs, "judgements": case_docs}
    elif table == "ordinances":
        docs["ordinances"] = ord_docs
    elif table == "judgements":
        docs["judgements"] = case_docs

    return docs


class Request(BaseModel):
    messages: List[ClientMessage]
    id: str


search_cap_tool = search_ordinance_or_regulation_tool(ord_table)
search_case_tool = search_cases_tool(judg_table)
available_tools = {
    search_cap_tool.get_tool_name(): search_cap_tool.run_tool,
    search_case_tool.get_tool_name(): search_case_tool.run_tool,
}

def do_stream(messages: List[ChatCompletionMessageParam], include_tools = True):
    stream = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        stream=True,
        temperature=0.1,
        max_tokens=16384,
        stream_options={"include_usage": True},
        tools=[search_cap_tool.get_function_schema(), search_case_tool.get_function_schema()] if include_tools else None,
        tool_choice="auto" if include_tools else None
    )

    return stream

def stream_search(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):
    # Check if the last message contains tool invocations
    has_tool_usage = False
    if messages and len(messages) > 0:
        last_message = messages[-1]
        if "tool_call_id" in last_message:
            has_tool_usage = True
    
    if not has_tool_usage:
        # Send search query first
        # search_query = get_search_query(client, MODEL, messages)
        # yield f'2:[{{"searchQuery":{json.dumps(search_query)}}}]\n'
        search_queries = query_expand(client, MODEL, messages)
        yield f'2:[{{"searchQueries":{json.dumps(search_queries)}}}]\n'
        
        # Send groundings next
        # groundings = search(search_query)
        groundings = search(search_queries, query_type="vector", top_k=4)
        yield f'2:[{{"groundings":{json.dumps(groundings)}}}]\n'
    else:
        # Skip search for tool usage rounds
        groundings = {}

    system_message = getQAPrompt(groundings)
    # Create streaming response from OpenAI
    stream = do_stream([{"role": "system", "content": system_message}] + messages)
    
    yield from process_stream_chunks(stream, available_tools)

def stream_consult(messages: List[ChatCompletionMessageParam], id: str, protocol: str = 'data'):
    # Ask for clarification in the first round
    if len(messages) == 1:
        stream = do_stream([{"role": "system", "content": getAskClarificationPrompt()}] + messages, include_tools = False)
        yield from process_stream_chunks(stream, available_tools)
        return
    
    # Check if grounding is needed
    if id not in kv or "groundings" not in kv[id]:
        queries = query_expand(client, MODEL, messages)
        yield f'2:[{{"searchQueries":{json.dumps(queries)}}}]\n'

        # Send groundings next
        groundings = search(queries, query_type="vector", top_k=3)
        yield f'2:[{{"groundings":{json.dumps(groundings)}}}]\n'

        kv[id] = {"groundings": groundings}
    groundings = kv[id]["groundings"]

    if "tasks" not in kv[id]:
        tasks = get_tasks(client, MODEL, messages, groundings)
        yield f'2:[{json.dumps({"tasks": tasks.model_dump()})}]\n'

        kv[id]["tasks"] = tasks
    tasks = kv[id]["tasks"]

    # Get first not completed task
    first_not_completed_task = next((task for task in tasks.tasks if not task.task_completed), None)
    if not first_not_completed_task:
        # use the chat agent
        stream = do_stream([{"role": "system", "content": getQAPrompt(groundings)}] + messages)
    else:
        stream = do_stream([{"role": "system", "content": getDoTaskPrompt(groundings, first_not_completed_task.task_description)}] + messages, include_tools = False)
        first_not_completed_task.task_completed = True
        yield f'2:[{json.dumps({"tasks": tasks.model_dump()})}]\n'
        kv[id]["tasks"] = tasks

    yield from process_stream_chunks(stream, available_tools)
    

    
@app.post("/api/chat")
async def handle_search_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)

    headers = { "x-vercel-ai-data-stream": "v1" }
    response = StreamingResponse(stream_search(openai_messages, protocol), media_type="text/plain", headers=headers)
    return response

@app.post("/api/consult")
async def handle_search_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    id = request.id
    openai_messages = convert_to_openai_messages(messages)

    headers = { "x-vercel-ai-data-stream": "v1" }
    response = StreamingResponse(stream_consult(openai_messages, id, protocol), media_type="text/plain", headers=headers)
    return response

@app.get("/api/exit")
async def handle_session_end(id: str = Query(None)):
    print(id)
    if id is None or id not in kv:
        raise HTTPException(status_code=404, detail="Session not found")
    del kv[id]
    return {"status": 200, "message": "Session ended successfully"}
