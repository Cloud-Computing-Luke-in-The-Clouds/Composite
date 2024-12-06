# config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    GCP_SERVICE_URL: str = "https://researcher-profile-265479170833.us-central1.run.app"
    gcp_mysql_connection_string: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()