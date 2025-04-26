from pydantic import BaseModel, Field
from typing import List

class QueryExpandFormat(BaseModel):
    
    queries: List[str] = Field(default_factory=list, description="A list of search queries")

schema = QueryExpandFormat()
print(schema.model_json_schema())
