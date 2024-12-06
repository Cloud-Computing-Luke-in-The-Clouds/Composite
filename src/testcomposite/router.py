# testing new composite that only uses HTTP
# router.py
from fastapi import APIRouter, HTTPException
from typing import List, Any, Dict
from .schemas import ResearchProfile, ResearcherComposite
from .service import ResearcherService

router = APIRouter()

@router.get("/researcher/{researcher_id}", response_model=Dict[str, Any])
async def get_researcher(researcher_id: int):
    service = ResearcherService()
    return await service.get_researcher(researcher_id)

@router.post("/researcher", status_code=201)
async def create_researcher(profile: ResearchProfile):
    service = ResearcherService()
    return await service.create_researcher(profile)

@router.put("/researcher/{researcher_id}")
async def update_researcher(researcher_id: int, profile: ResearchProfile):
    service = ResearcherService()
    return await service.update_researcher(researcher_id, profile)