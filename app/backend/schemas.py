from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class VacancyIn(BaseModel):
    title: str
    description: str
    weights: Dict[str, float] = Field(default_factory=dict)

class ResumeOut(BaseModel):
    text: str
    skills: List[str] = Field(default_factory=list)           # ← фикс мутируемого дефолта
    contact: Optional[Dict[str, str]] = None

# одна строка таблицы предскрининга
class PrescreenItem(BaseModel):
    skill: str
    weight: float
    have: bool                         # ← добавили (для фронта)
    in_resume: bool                    # ← оставили для совместимости
    score: float                       # ← добавили (чтобы не было undefined)
    note: Optional[str] = None

class PrescreenOut(BaseModel):
    table: List[PrescreenItem]
    top_missing: List[str] = Field(default_factory=list)       # ← фикс дефолта

class Evidence(BaseModel):
    skill: str
    quote: str
    t: float  # timecode sec

class ReportIn(BaseModel):
    vacancy: VacancyIn
    resume: ResumeOut
    evidences: List[Evidence] = Field(default_factory=list)    # ← фикс дефолта

class ReportOut(BaseModel):
    score: float
    flags: List[str]
    url_pdf: Optional[str] = None
