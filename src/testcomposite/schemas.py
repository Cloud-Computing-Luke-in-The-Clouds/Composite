# composite/schemas.py
from typing import List, Optional
from pydantic import BaseModel

class Citation(BaseModel):
    paper_id: int
    cited_by: int
    year: int

class ResearchMetrics(BaseModel):
    h_index: int
    total_citations: int
    i10_index: int

# original researcher schemas
class ResearchPaper(BaseModel):
    paper_title: Optional[str] = None
    paper_link: Optional[str] = None
    demo_video_link: Optional[str] = None
    project_website: Optional[str] = None

class ResearchProfile(BaseModel):
    google_scholar_link: Optional[str] = None
    personal_website_link: Optional[str] = None
    organization: Optional[str] = None
    # title: Optional[str] = None
    # age: Optional[int] = None
    # sex: Optional[str] = None
    title: str
    age: int
    sex: str
#   paper: Optional[list[ResearchPaper]] = None

# composite that depend on researcher schema
class ResearcherComposite(BaseModel):
    profile: ResearchProfile
    papers: Optional[List[ResearchPaper]] = None
    metrics: Optional[ResearchMetrics] = None
    citations: Optional[List[Citation]] = None