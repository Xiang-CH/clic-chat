import json
from typing import Literal

import lancedb
from cachetools import cached
from dotenv import load_dotenv
from flask import Flask, request
from lancedb.embeddings import get_registry, TextEmbeddingFunction
from lancedb.rerankers import RRFReranker
from langchain_openai import AzureOpenAIEmbeddings

app = Flask(__name__)
app.debug = True
load_dotenv()


@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"


registry = get_registry()


@registry.register("azure-openai")
class AzureOpenAIEmbeddingsFunction(TextEmbeddingFunction):
    name: str = "embedding"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ndims = None

    def generate_embeddings(self, texts):
        return self._embedding_model().embed_documents(texts)

    def ndims(self):
        if self._ndims is None:
            self._ndims = len(self.generate_embeddings("foo")[0])
        return self._ndims

    @cached(cache={})
    def _embedding_model(self):
        return AzureOpenAIEmbeddings(model="embedding")


# azure_openai = registry.get("azure-openai").create()
# embedding_function = AzureOpenAIEmbeddings(model="embedding")

def search_db(query, query_type: Literal["vector", "fts", "hybrid", "auto"] = "hybrid"):
    db = lancedb.connect("../db")
    table = db.open_table("ordinances")

    if query_type == "hybrid":
        reranker = RRFReranker(return_score="all")
        docs = table.search(query, query_type=query_type).limit(10).rerank(reranker=reranker).to_pandas()[
            ["text", "cap_no", "cap_title", "url", "_relevance_score"]]
    else:
        docs = table.search(query, query_type=query_type, fts_columns="text").limit(10).to_pandas()

    return docs.to_json(orient="records")


@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get('q')
    if not query:
        return "No query provided", 400

    return search_db(query, query_type="fts"), 200


@app.route('/stream', methods=['POST'])
def ask():
    body = request.form
    conversation = json.loads(request.form.get('conversation'))

    if not conversation:
        return "No conversation provided", 400
    elif conversation[-1]["role"] != "user":
        return "Last message must be from user", 400

    query = conversation[-1]["content"]

    def iter_data():
        # Return the search results as a stream
        yield search_db(query)

    return iter_data(), {'Content-Type': 'text/event-stream'}
