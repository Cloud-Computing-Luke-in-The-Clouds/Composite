# composite/schemas.py
from typing import List, Optional
from pydantic import BaseModel  # FastAPI
from ..researcher.schemas import ResearchProfile, ResearchPaper

class Citation(BaseModel):
    paper_id: int
    cited_by: int
    year: int

class ResearchMetrics(BaseModel):
    h_index: int
    total_citations: int
    i10_index: int

class ResearcherComposite(BaseModel):
    profile: ResearchProfile
    papers: Optional[List[ResearchPaper]] = None
    metrics: Optional[ResearchMetrics] = None
    citations: Optional[List[Citation]] = None