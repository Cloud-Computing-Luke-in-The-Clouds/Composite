from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseName, UseOptionalParams, UseAdditionalFields
from src.researcher.models import ResearchProfile as ResearchProfileModel
from src.researcher.schemas import ResearchProfile
from sqlalchemy.orm import Session
import httpx
from . import service
from src.database import get_db
import time
from typing import Optional, List
import requests

router = APIRouter()

# By HTTP requests - GET
@router.get("/researcher1/{researcher_id}")
async def get_researcher_composite(
    researcher_id: int,
    include_papers: bool = Query(
        True, 
        description="Include research papers"
    ),
    include_scholar_metrics: bool = Query(
        True, 
        description="Include Google Scholar metrics"
    ),
    db: Session = Depends(get_db)
):
    """
    GET endpoint that fetches:
    - Base researcher profile
    - Research papers (optional)
    - Google Scholar metrics (optional)
    """
    researcher_service = service.ResearcherCompositeService(db)  # Initialize with proper service class
    
    # Use httpx for async HTTP requests instead of requests
    async with httpx.AsyncClient(timeout=30.0) as client:  # Added timeout
        try:
            # It's recommended to use environment variables for the base URL
            response = await client.get(f'http://localhost:8000/researcher/{researcher_id}')
            response.raise_for_status()
            researcher_data = response.json()
            
            result = await researcher_service.get_researcher_composite(
                researcher_id=researcher_id,
                base_profile=researcher_data,
                include_papers=include_papers,
                include_scholar_metrics=include_scholar_metrics
            )
            
            if result is None:
                raise HTTPException(status_code=404, detail="Researcher not found")
                
            return result
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching researcher data: {str(e)}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

# By HTTP requests - POST
@router.post("/researcher1", status_code=201)
async def create_researcher_composite(
    research_profile: ResearchProfile,
    db: Session = Depends(get_db)
):
    """
    POST endpoint that creates a researcher profile in both services:
    - Creates in the local database
    - Creates in the remote service (port 8000)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Convert Pydantic model to dict for the remote service
            profile_dict = research_profile.dict()
            
            # First, create in remote service
            remote_response = await client.post(
                'http://localhost:8000/researcher',
                json=profile_dict
            )
            remote_response.raise_for_status()
            remote_data = remote_response.json()

            # Then create in local database (not async)
            local_profile = service.create_research_profile(db, research_profile)
            
            return {
                "local_id": local_profile.id,
                "remote_id": remote_data.get("id"),
                "message": "Researcher profile created successfully in both services",
                "links": {
                    "local": f"/researcher1/{local_profile.id}",
                    "remote": remote_data.get("link", "")
                }
            }

        except httpx.HTTPStatusError as e:
            # If remote creation fails, don't create locally
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error creating researcher in remote service: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating researcher: {str(e)}"
            )

# By HTTP requests - PATCH
@router.patch("/researcher1/{researcher_id}")
async def update_researcher_composite(
    researcher_id: int,
    research_profile: ResearchProfile,
    db: Session = Depends(get_db)
):
    """
    PATCH endpoint that updates a researcher profile in both services:
    - Updates in the local database
    - Updates in the remote service (port 8000)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Convert Pydantic model to dict
            profile_dict = research_profile.dict(exclude_unset=True)
            
            # First, update in remote service using PATCH
            remote_response = await client.patch(
                f'http://localhost:8000/researcher/{researcher_id}',
                json=profile_dict
            )
            remote_response.raise_for_status()

            # Then update in local database
            local_profile = service.update_research_profile(db, researcher_id, research_profile)
            if not local_profile:
                raise HTTPException(status_code=404, detail="Researcher not found in local database")

            return {
                "local_id": local_profile.id,
                "message": "Researcher profile updated successfully in both services",
                "updated_profile": {
                    "google_scholar_link": local_profile.google_scholar_link,
                    "personal_website_link": local_profile.personal_website_link,
                    "organization": local_profile.organization,
                    "title": local_profile.title,
                    "age": local_profile.age,
                    "sex": local_profile.sex
                }
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error updating researcher in remote service: {str(e)}"
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

# By HTTP requests - PUT
@router.put("/researcher2/{researcher_id}")
async def update_researcher_composite(
    researcher_id: int,
    research_profile: ResearchProfile,
    db: Session = Depends(get_db)
):
    """
    PUT endpoint that updates a researcher profile in both services:
    - Updates in the local database
    - Updates in the remote service (port 8000)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # First, update in remote service
            remote_response = await client.put(
                f'http://localhost:8000/researcher/{researcher_id}',
                json=research_profile.dict()
            )
            remote_response.raise_for_status()

            # Then update in local database
            existing_profile = service.get_research_profile_by_id(db, researcher_id)
            if not existing_profile:
                raise HTTPException(status_code=404, detail="Researcher not found in local database")

            # Update local profile fields
            for field, value in research_profile.dict(exclude_unset=True).items():
                setattr(existing_profile, field, value)

            db.commit()
            db.refresh(existing_profile)

            return {
                "local_id": existing_profile.id,
                "remote_response": remote_response.json(),
                "message": "Researcher profile updated successfully in both services"
            }

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error updating researcher in remote service: {str(e)}"
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

# support navigation path
# should use http but currently using db
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

# synchronous
@router.get("/researcher1_sync/{researcher_id}")
def get_researcher_composite_sync(
    researcher_id: int,
    include_papers: bool = Query(True, description="Include research papers"),
    include_scholar_metrics: bool = Query(True, description="Include Google Scholar metrics"),
    db: Session = Depends(get_db)
):
    try:
        response = requests.get(f'http://localhost:8000/researcher/{researcher_id}')
        response.raise_for_status()
        researcher_data = response.json()
        
        researcher_service = service.ResearcherCompositeService(db)
        result = researcher_service.get_researcher_composite_sync(
            researcher_id=researcher_id,
            base_profile=researcher_data,
            include_papers=include_papers,
            include_scholar_metrics=include_scholar_metrics
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="Researcher not found")
            
        return result
        
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching researcher data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# original GET/PUT/POST on db
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

