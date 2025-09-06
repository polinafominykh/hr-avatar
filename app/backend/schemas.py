from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class VacancyIn(BaseModel):
    title: str
    description: str
    weights: Dict[str, float] = Field(default_factory=dict)

class ResumeOut(BaseModel):
    text: str
    skills: List[str] = []
    contact: Optional[Dict[str, str]] = None

class PrescreenItem(BaseModel):
    skill: str
    in_resume: bool
    weight: float
    note: Optional[str] = None

class PrescreenOut(BaseModel):
    table: List[PrescreenItem]
    top_missing: List[str] = []

class Evidence(BaseModel):
    skill: str
    quote: str
    t: float  # timecode sec

class ReportIn(BaseModel):
    vacancy: VacancyIn
    resume: ResumeOut
    evidences: List[Evidence] = []

class ReportOut(BaseModel):
    score: float
    flags: List[str]
    url_pdf: Optional[str] = None
