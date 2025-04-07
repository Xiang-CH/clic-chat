from typing import Literal, List
from pydantic import BaseModel, Field

class Law(BaseModel):
    name: str = Field(description="The full name of the ordinance/regulation/case")
    quote: str = Field(description="Quote of the referred materials")
    cap_no: str = Field(default="", description="The cap number of the ordinance/regulation")
    section_no: str = Field(default="", description="The section number of the ordinance/regulation")

class CaseMeta(BaseModel):
    case_type: Literal["civic", "criminal"] = Field(description="Where it is a civic case or a criminal case")
    crime_name: str = Field(description="Specific name of the crime or offence or disbute")
    case_summary: str = Field(description="Comprehensive summary of the case covering all aspects.")
    court_decision: str = Field(description="Decision of the case")
    case_causes: str = Field(description="Causes of the case")
    case_evidence: str = Field(description="Evidence of the case")
    # law_citations: List[Law] = Field(default=[], description="Ordinances/Regulations or other cases cited in the case")
    