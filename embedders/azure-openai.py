from cachetools import cached
from langchain_openai import AzureOpenAIEmbeddings
from lancedb.embeddings import get_registry, TextEmbeddingFunction

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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

