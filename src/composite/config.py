# config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict

class Settings(BaseSettings):
    GCP_SERVICE_URL: str = "https://researcher-profile-265479170833.us-central1.run.app"
    gcp_mysql_connection_string: Optional[str] = None
    WORKFLOW_TOKEN: Optional[str] = None
    # email
    SMTP_SERVER: str
    SMTP_PORT: int
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    # Store like_map in a more structured way
    LIKE_MAP: Dict[str, list] = {}

    class Config:
        env_file = ".env"

settings = Settings()