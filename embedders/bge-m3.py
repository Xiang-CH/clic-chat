import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry

db = lancedb.connect("/tmp/db")
model = get_registry().get("sentence-transformers").create(name="BAAI/bge-m3", device="mps")

class Words(LanceModel):
    text: str = model.SourceField()
    vector: Vector(model.ndims()) = model.VectorField()

table = db.create_table("words", schema=Words)
table.add(
    [
        {"text": "hello world"},
        {"text": "goodbye world"}
    ]
)

query = "greetings"
actual = table.search(query).limit(1).to_pydantic(Words)[0]
print(actual.text)