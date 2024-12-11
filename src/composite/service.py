# service.py
from fastapi import HTTPException
import httpx
from typing import Optional, Dict, Any
import logging
from .config import settings
from .models import ResearchProfile
import requests
# pagination
from fastapi_pagination.ext.sqlalchemy import paginate
# email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
    
    async def get_researcher_name(self, researcher_id: int) -> str:
        """Fetch only researcher name from GCP service"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/researcher/{researcher_id}"
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract just the researcher_name
                return data.get("researcher_name")
                
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
    
    async def get_all_researchers(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Fetch all researchers from GCP service with pagination"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # without pagination
                response = await client.get(
                    f"{self.base_url}/researchers",
                    params={"skip": skip, "limit": limit}
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error fetching researchers: {str(e)}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Service unavailable: {str(e)}"
                )
    
    def get_all_researchers_sync(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Fetch all researchers from GCP service with pagination (sync)"""
        try:
            # without pagination
            response = requests.get(
                f"{self.base_url}/researchers",
                params={"skip": skip, "limit": limit},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error fetching researchers: {str(e)}"
            )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {str(e)}"
            )

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.email_user = settings.EMAIL_USER
        self.email_password = settings.EMAIL_PASSWORD

    async def send_match_notification(self, recipient_email: str, researcher_email: str, correlation_id: str) -> bool:
        """Send a match notification email"""
        try:
            # sending email 1 to user
            logger.info(f"Correlation ID: {correlation_id}, Sending match notification to {recipient_email}")
            
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = recipient_email
            msg["Subject"] = "New Research Match!"

            body = f"""
            Hi,
            
            Great news! You and Researcher {researcher_email} have matched based on your research interests.
            
            Best regards,
            Luke In The Clouds Research Team
            """
            
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"Correlation ID: {correlation_id}, Email sent successfully to {recipient_email}")

            # sending email 2 to user
            logger.info(f"Correlation ID: {correlation_id}, Sending match notification to {recipient_email}")
            
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = researcher_email
            msg["Subject"] = "New Research Match!"

            body = f"""
            Hi,
            
            Great news! You and User {recipient_email} have matched based on your research interests.
            
            Best regards,
            Luke In The Clouds Research Team
            """
            
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            logger.info(f"Correlation ID: {correlation_id}, Email sent successfully to {researcher_email}")

            return {"message": "Email sent successfully"}

        except Exception as e:
            logger.error(f"Correlation ID: {correlation_id}, Failed to send email: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {str(e)}"
            )