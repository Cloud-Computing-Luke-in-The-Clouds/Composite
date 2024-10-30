from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseName, UseOptionalParams, UseAdditionalFields
from src.researcher.models import ResearchProfile as ResearchProfileModel  # Renamed to avoid confusion
from src.researcher.schemas import ResearchProfile
from sqlalchemy.orm import Session
from . import service
from src.database import get_db
import time
from typing import Optional, List

router = APIRouter()

@router.get("/researchers", response_model=CustomizedPage[
    Page[ResearchProfile],
    UseAdditionalFields(
        link=str,
    ),
])
async def get_all_researchers(db: Session = Depends(get_db)):
    
    profiles = service.get_all_research_profiles(db)
    
    link_header = []
    page = profiles.page
    size = profiles.size
    pages = profiles.pages

    # Previous link: Check if there is a previous page
    if page > 1:
        prev_page = page - 1
        link_header.append(
            f'<{router.url_path_for("get_all_researchers")}?page={prev_page}&size={size}>; rel="prev"'
        )

    # Next link: Check if there is a next page
    if page < pages:
        next_page = page + 1
        link_header.append(
            f'<{router.url_path_for("get_all_researchers")}?page={next_page}&size={size}>; rel="next"'
        )

    # Add Link header to the response if any links were created
    if link_header:
        profiles.link = ", ".join(link_header)

    return profiles


@router.get("/researcher/{researcher_id}")
async def get_researcher_by_id(
    researcher_id: int,
    db: Session = Depends(get_db)
):
    return service.get_research_profile_by_id(db, researcher_id)


@router.delete("/researcher/{researcher_id}")
async def delete_researcher_by_id(
    researcher_id: int,
    db: Session = Depends(get_db)
):
    return service.delete_research_profile_by_id(db, researcher_id)


@router.post("/researcher", status_code=201)
async def creat_new_researcher(research_profile: ResearchProfile,
                               db: Session = Depends(get_db)):
    
    response = service.create_research_profile(db, research_profile)

    return {'link': f"{router.url_path_for('get_researcher_by_id', researcher_id = response.id)}; rel='self'"}

@router.post("/background_add_researcher", status_code=202)
async def background_add_new_researcher(research_profile: ResearchProfile, background_tasks: BackgroundTasks,
                               db: Session = Depends(get_db)):
    
    background_tasks.add_task(time.sleep, 30)
    background_tasks.add_task(service.create_research_profile, db, research_profile)

    return {'message': 'Research profile creation in progress.'}

@router.patch("/researcher/{researcher_id}")
async def update_researcher_by_id(
    researcher_id: int,
    research_profile: ResearchProfile,
    db: Session = Depends(get_db)
):
    updated_profile = service.update_research_profile(db, researcher_id, research_profile)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return updated_profile

@router.put("/researcher/{researcher_id}")
async def update_researcher_full(
    researcher_id: int,
    research_profile: ResearchProfile,
    db: Session = Depends(get_db)
):
    """
    PUT endpoint for full resource replacement
    """
    updated_profile = service.update_research_profile(db, researcher_id, research_profile, partial=False)
    if not updated_profile:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return updated_profile

# support navigation path
@router.get("/researcher3/{organization}/{role}", response_model=List[ResearchProfile])
async def search_researchers(
    organization: str,
    role: str,
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(ResearchProfileModel).filter(
            ResearchProfileModel.organization == organization,
            ResearchProfileModel.title == role
        )
        
        if min_age is not None:
            query = query.filter(ResearchProfileModel.age >= min_age)
        if max_age is not None:
            query = query.filter(ResearchProfileModel.age <= max_age)
            
        results = query.all()
        if not results:
            raise HTTPException(status_code=404, detail="No researchers found matching the criteria")
            
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")