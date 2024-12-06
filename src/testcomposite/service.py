# service.py
from fastapi import HTTPException
import httpx
from typing import Optional, Dict, Any
import logging
from .config import settings
from .models import ResearchProfile

logger = logging.getLogger(__name__)

class ResearcherService:
    def __init__(self):
        self.base_url = settings.GCP_SERVICE_URL
        
    async def get_researcher(self, researcher_id: int) -> Dict[str, Any]:
        """Fetch researcher data from GCP service"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/researcher/{researcher_id}"
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"GCP service error: {str(e)}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Service unavailable: {str(e)}"
                )

    async def create_researcher(self, profile: ResearchProfile) -> Dict[str, Any]:
        """Create researcher in GCP service"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/researcher",
                    json=profile.dict()
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error creating researcher: {str(e)}"
                )

    async def update_researcher(self, researcher_id: int, profile: ResearchProfile) -> Dict[str, Any]:
        """Update researcher in GCP service"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(
                    f"{self.base_url}/researcher/{researcher_id}",
                    json=profile.dict(exclude_unset=True)
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error updating researcher: {str(e)}"
                )