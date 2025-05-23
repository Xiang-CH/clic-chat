from cachetools import cached
from dotenv import load_dotenv

from langchain_community.vectorstores import LanceDB
from langchain_openai import AzureOpenAIEmbeddings

import lancedb
from lancedb.embeddings import get_registry, TextEmbeddingFunction
from lancedb.rerankers import RRFReranker

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

azure_openai = registry.get("azure-openai").create()

load_dotenv()
embedding_function = AzureOpenAIEmbeddings(model="embedding")

db = lancedb.connect("../db")

print(db.table_names())
table = db.open_table("ordinances")

query = "what can i do if my landlord is not fixing things"
reranker = RRFReranker(return_score="all")
docs = table.search(query, query_type="hybrid").limit(5).rerank(reranker=reranker).to_pandas()[["text", "_distance", "_score", "_relevance_score"]]
print(docs)


