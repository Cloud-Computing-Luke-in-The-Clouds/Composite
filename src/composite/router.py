# testing new composite that only uses HTTP
# router.py
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Any, Dict
from .schemas import ResearchProfile, ResearcherComposite
from .service import ResearcherService, EmailService
from .config import settings
import json

# pagination
from fastapi_pagination import Page
# email, logging
from pydantic import EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
# pubsub, workflow
import requests
from google.cloud import pubsub_v1

router = APIRouter()

# email
logger = logging.getLogger(__name__)
# pubsub, workflow
token = "ya29.a0AeDClZD7hnPemu9m408a8SOEgiHU_QbFg_lPsanjFkmTgpG7U8a9u3_Yar83r-P6QbC0ohmJ6xlOj7xs_fZGyuPNqoI127NxCchvJzkJ1Pb0jh1xsRWkec3vhR-t5aEWb1urMPz6UVyEXs2gdWdZBeQZtad9FHW0_taWQEknx6hG5TCNPkT80n-iwY8KMPi3YOSFJq2poqULiqhwsCirNfjpAhbGGkmLeWMiqHLWWxDbIb3_pTVw7g23tdDZ0Cy_eDlIFdlfG9Pd7UJ3wxT4qyjz3ASUyeMT_XaXgOfQ-O2codtbFoMVbgAsmPF5mJL6G10qEqoKRHucbXjYC1TctqmHFezw5sFejbh4zofiSu74QIElz49RF6HO60MqEqyPrAn6JdUgpX0ddUPezVC_xYh0zfIoGNy7lktyaCgYKAdwSARESFQHGX2Mi6vvuqhHe-sLrpUGPe5zROg0427"

@router.get("/researcher/{researcher_id}", response_model=Dict[str, Any])
async def get_researcher(researcher_id: int):
    service = ResearcherService()
    return await service.get_researcher(researcher_id)

@router.get("/researcher/{researcher_id}/name", response_model=str)
async def get_researcher_name(researcher_id: int):
    """Get just the researcher name"""
    service = ResearcherService()
    return await service.get_researcher_name(researcher_id)

# @router.post("/researcher", status_code=201)
# async def create_researcher(profile: ResearchProfile):
#     service = ResearcherService()
#     return await service.create_researcher(profile)

# @router.put("/researcher/{researcher_id}")
# async def update_researcher(researcher_id: int, profile: ResearchProfile):
#     service = ResearcherService()
#     return await service.update_researcher(researcher_id, profile)

# get all researchers.
@router.get("/researchers_async")
async def get_all_researchers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)
):
    """Async endpoint to get all researchers"""
    service = ResearcherService()
    return await service.get_all_researchers(skip=skip, limit=limit)

@router.get("/researchers_sync")
def get_all_researchers_sync(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100)
):
    """Sync endpoint to get all researchers"""
    service = ResearcherService()
    return service.get_all_researchers_sync(skip=skip, limit=limit)

# like match and email
email_service = EmailService()
@router.post("/like_researcher/")
async def like_researcher(
    request: Request,
    user_email: str,
    researcher_email: str,
    researcher_name: str
):
    """
    Handle researcher like action and send notification if there's a match.
    Corresponding credentials are saved in .env. Including SMTP and LIKE_MAP.
    """
    correlation_id = request.state.correlation_id
    
    try:
        # Get the current likes for the researcher
        researcher_likes = settings.LIKE_MAP.get(researcher_email, [])
        
        # Check if user has already liked
        if user_email in researcher_likes:
            # It's a match! Send email notification to user
            return await email_service.send_match_notification(
                user_email,
                researcher_name,
                correlation_id
            )
        else:
            # Add to likes
            if researcher_email not in settings.LIKE_MAP:
                settings.LIKE_MAP[researcher_email] = []
            settings.LIKE_MAP[researcher_email].append(user_email)
            return {"message": "Like recorded successfully"}

    except Exception as e:
        logger.error(f"Correlation ID: {correlation_id}, Error in like_researcher: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing like: {str(e)}"
        )