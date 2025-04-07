import asyncio
import os
import json
import lancedb
import re
from typing import List, Literal
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AzureOpenAI
from .utils.prompt import ClientMessage, convert_to_openai_messages
from .utils.tools import get_current_weather

from .helper import get_search_query
from .prompts import getQAPrompt


# load_dotenv(".env.local")
load_dotenv()

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
ord_table = db.open_table("ordinances")
judg_table = db.open_table("judgements")


class Request(BaseModel):
    messages: List[ClientMessage]


available_tools = {
    "get_current_weather": get_current_weather,
}

def do_stream(messages: List[ChatCompletionMessageParam]):
    stream = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        stream=True,
        # tools=[{
        #     "type": "function",
        #     "function": {
        #         "name": "get_current_weather",
        #         "description": "Get the current weather at a location",
        #         "parameters": {
        #             "type": "object",
        #             "properties": {
        #                 "latitude": {
        #                     "type": "number",
        #                     "description": "The latitude of the location",
        #                 },
        #                 "longitude": {
        #                     "type": "number",
        #                     "description": "The longitude of the location",
        #                 },
        #             },
        #             "required": ["latitude", "longitude"],
        #         },
        #     },
        # }]
    )

    return stream

def stream_search(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):

    # Send search query first
    search_query = get_search_query(client, MODEL, messages)
    yield f'2:[{{"searchQuery":{json.dumps(search_query)}}}]\n'
    # await asyncio.sleep(0)
    
    # Send groundings next
    groundings = search(search_query)
    yield f'2:[{{"groundings":{json.dumps(groundings)}}}]\n'
    # await asyncio.sleep(0)

    system_message = getQAPrompt(groundings)
    # Create streaming response from OpenAI
    stream = client.chat.completions.create(
        messages=[{"role": "system", "content": system_message}] + messages,
        model=MODEL,
        stream=True,
    )
    
    for chunk in stream:
        for choice in chunk.choices:
            if choice.delta.content:
                yield f'0:{json.dumps(choice.delta.content)}\n'
            
            if choice.finish_reason:
                yield f'd:{{"finishReason":"{choice.finish_reason}"}}\n'



def search(query, table = "both", top_k = 6, query_type: Literal["vector", "fts", "hybrid", "auto"] = "hybrid"):
    # table = db.open_table("judgements")
    if table == "ordinances" or table == "both":
        ord_docs = ord_table.search(query, query_type=query_type, fts_columns="text").limit(top_k).select(["cap_no", "section_no", "type", "cap_title", "section_heading", "text", "url"]).to_list()
    if table == "judgements" or table == "both":
        case_docs = judg_table.search(query, query_type=query_type, fts_columns="case_summary").select(["crime_name", "case_type", "court", "case_name","case_summary","date","case_number", "case_causes", "court_decision", "url"]).limit(top_k).to_list()
        for doc in case_docs:
            doc["date"] = doc["date"].strftime("%Y-%m-%d")
    
    docs = {}
    if table == "both":
        docs = {"ordinances": ord_docs, "judgements": case_docs}
    elif table == "ordinances":
        docs["ordinances"] = ord_docs
    elif table == "judgements":
        docs["judgements"] = case_docs

    return docs



@app.post("/api/chat")
async def handle_search_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)

    headers = {
        # "Cache-Control": "no-cache",
        # "Connection": "keep-alive",
        # "Transfer-Encoding": "chunked",
        "x-vercel-ai-data-stream": "v1",
    }
    response = StreamingResponse(stream_search(openai_messages, protocol), media_type="text/plain", headers=headers)
    return response
