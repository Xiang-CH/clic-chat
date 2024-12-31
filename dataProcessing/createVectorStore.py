from cachetools import cached
from dotenv import load_dotenv

from langchain_community.vectorstores import LanceDB
from langchain_openai import AzureOpenAIEmbeddings

import os
import lancedb
import pandas as pd
from lancedb.embeddings import get_registry, TextEmbeddingFunction
from lancedb.pydantic import Vector, LanceModel

load_dotenv()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

embedding_function = AzureOpenAIEmbeddings(model="embedding")

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
db = lancedb.connect("../db")

# class AzureOpenaiVector(Vector):
#     def __init__(self):
#         super().__init__(dims=azure_openai.ndims())


class OrdinanceSchema(LanceModel):
    text: str = azure_openai.SourceField()
    vector: Vector(dim=azure_openai.ndims()) = azure_openai.VectorField() # type: ignore
    lang: str
    cap_no: int
    section_no: str
    type: str
    url: str
    cap_title: str
    section_heading: str

# Find and convert string values in the 'vector' column to lists of floats
def convert_vector(vector):
    if isinstance(vector, str):
        return list(map(float, vector.strip('[]').split(',')))
    return vector

# table = db.create_table(
#         name = "ordinances",
#         schema = OrdinanceSchema,
#         mode = "overwrite",
#     )
table = db.open_table("ordinances")

# for lang in ["en", "sc", "tc"]:
#     df = pd.read_csv(f"vectorData/ordinances_{lang}.csv")
#     df["vector"] = df["vector"].apply(convert_vector)
#     df["lang"] = lang
#     print(df.info())

#     table.add(df)


table.create_fts_index("text", use_tantivy=False)

query = "Copyright"
docs = table.search(query=query, query_type="fts", fts_columns="text").limit(5).to_pandas()["text"].to_list()
print(docs)


