from typing import Literal, List
from pydantic import BaseModel, Field

class Law(BaseModel):
    cap_no: str = Field(description="Cap number of the law in the form of 'Cap xx'")
    name: str = Field(description="Name of the ordinance or regulation")
    sections: List[str] = Field(default=[], description="Sections number in the cap in the form of 'Section xx'")

class CaseMeta(BaseModel):
    case_type: Literal["civic", "criminal"] = Field(description="Where it is a civic case or a criminal case")
    crime: str = Field(description="Specific crimes or legal relations within the domain")
    case_summary: str = Field(description="Comprehensive summary of the case covering all aspects. (~200 words)")
    case_punishment: str = Field(description="Punishment of the case")
    case_causes: str = Field(description="Causes of the case")
    case_evidence: str = Field(description="Evidence of the case")
    laws: List[Law] = Field(description="Legislation (caps) referred in the case")
    
