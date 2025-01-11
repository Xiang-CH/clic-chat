import json
import os
from typing import Literal

import lancedb
# from cachetools import cached
from dotenv import load_dotenv
from flask import Flask, request
# from lancedb.embeddings import get_registry, TextEmbeddingFunction
from lancedb.rerankers import RRFReranker

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.debug = True
load_dotenv()
db = lancedb.connect("../../db/lancedb")

@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"

def search_ord(query, top_k = 10, query_type: Literal["vector", "fts", "hybrid", "auto"] = "hybrid"):
    table = db.open_table("ordinances")

    if query_type == "hybrid":
        reranker = RRFReranker(return_score="all")
        docs = table.search(query, query_type=query_type).limit(top_k).rerank(reranker=reranker).to_pandas()[
            ["text", "cap_no", "cap_title", "url", "_relevance_score"]]
    else:
        docs = table.search(query, query_type=query_type, fts_columns="text").limit(top_k).to_pandas()

    return docs.to_json(orient="records")

def search_judg(query, top_k = 10, query_type: Literal["vector", "fts", "hybrid", "auto"] = "hybrid"):
    table = db.open_table("judgements")

    if query_type == "hybrid":
        reranker = RRFReranker(return_score="all")
        docs = table.search(query, query_type=query_type).limit(top_k).rerank(reranker=reranker).to_pandas()[
            ["text", "case_name", "case_number", "date", "court", "_relevance_score"]]
    else:
        docs = table.search(query, query_type=query_type, fts_columns="text").limit(top_k).to_pandas()

    return docs.to_json(orient="records")


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get('q')
    if not query:
        return "No query provided", 400

    return search_ord(query, top_k=10, query_type="fts"), 200


@app.route("/retrieval", methods=["POST"])
def retrieval():
    body = request.json

    knowledge_id = body.get("knowledge_id")
    query = body.get("query")
    retrieval_setting = body.get("retrieval_setting")

    if not query:
        return "No query provided", 400
    
    if knowledge_id == "ordinances":
        return search_ord(query, retrieval_setting["top_k"], query_type="hybrid"), 200
    elif knowledge_id == "judgements":
        return search_judg(query, retrieval_setting["top_k"], query_type="hybrid"), 200
    else:
        return "Invalid knowledge_id", 400




# @app.route('/stream', methods=['POST'])
# def ask():
#     body = request.form
#     conversation = json.loads(request.form.get('conversation'))

#     if not conversation:
#         return "No conversation provided", 400
#     elif conversation[-1]["role"] != "user":
#         return "Last message must be from user", 400

#     query = conversation[-1]["content"]

#     def iter_data():
#         # Return the search results as a stream
#         yield search_db(query)

#     return iter_data(), {'Content-Type': 'text/event-stream'}
