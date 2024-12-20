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
import os
import time

router = APIRouter()

# email
logger = logging.getLogger(__name__)
# pubsub, workflow
# token = "ya29.a0AeDClZD7hnPemu9m408a8SOEgiHU_QbFg_lPsanjFkmTgpG7U8a9u3_Yar83r-P6QbC0ohmJ6xlOj7xs_fZGyuPNqoI127NxCchvJzkJ1Pb0jh1xsRWkec3vhR-t5aEWb1urMPz6UVyEXs2gdWdZBeQZtad9FHW0_taWQEknx6hG5TCNPkT80n-iwY8KMPi3YOSFJq2poqULiqhwsCirNfjpAhbGGkmLeWMiqHLWWxDbIb3_pTVw7g23tdDZ0Cy_eDlIFdlfG9Pd7UJ3wxT4qyjz3ASUyeMT_XaXgOfQ-O2codtbFoMVbgAsmPF5mJL6G10qEqoKRHucbXjYC1TctqmHFezw5sFejbh4zofiSu74QIElz49RF6HO60MqEqyPrAn6JdUgpX0ddUPezVC_xYh0zfIoGNy7lktyaCgYKAdwSARESFQHGX2Mi6vvuqhHe-sLrpUGPe5zROg0427"

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
                researcher_email,
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
    

@router.post("/workflow_example/")
async def pubsub():
    import threading
    """ 
    Would need to first load the credential
    Replace the token value in the env variable using the following command
    """
    # export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
    # gcloud auth application-default print-access-token

    workflow_url = "https://workflowexecutions.googleapis.com/v1/projects/coms-4153-cloud-computing/locations/us-central1/workflows/workflow-1/executions"
    token = os.getenv("WORKFLOW_TOKEN")

    payload = {
        "argument": '{"scholarLink": "https://scholar.google.com/citations?user=l2g4PFYAAAAJ&hl=en"}'
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(workflow_url, headers=headers, json=payload)

    if response.status_code == 200:
        execution_id = response.json()['name'].split('/')[-1]  # 提取 execution ID
        print(f"Workflow started successfully. Execution ID: {execution_id}")
    else:
        print(f"Failed to start workflow execution: {response.text}")
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = "projects/coms-4153-cloud-computing/subscriptions/pubsub-sub"

    stop_event = threading.Event()

    def callback(message):
        print(f"Received message: {message.data.decode('utf-8')}")
        message.ack()
        stop_event.set()

    print(f"Listening on {subscription_path}")
    try:
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

        # Run the subscriber in a separate thread to allow graceful stopping
        subscriber_thread = threading.Thread(target=streaming_pull_future.result)
        subscriber_thread.start()

        # Wait for the stop event
        stop_event.wait()

        # Cancel the subscriber when the stop event is set
        streaming_pull_future.cancel()
        subscriber_thread.join()

    except Exception as e:
        print(f"Subscriber error: {e}")

    return 

@router.post("/external_cloud_service/")
async def get_wikipedia_summary(title):
    """
    Fetches the summary of a Wikipedia page by its title.

    :param title: The title of the Wikipedia page (e.g., "GraphQL")
    :return: A string containing the summary or an error message.
    """
    url = "https://en.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": title
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_content in pages.items():
            if page_id == "-1":
                return f"Error: Page '{title}' not found."
            return page_content.get("extract", "No summary available.")
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
