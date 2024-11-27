# Composite Service
## Researcher-Service Installation Guide

### Installation Methods


1. Create and activate a Python virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   ```

2. Fill in .env
    ```
    cp .env-example .env
   ```
   fill in GCP_MYSQL_CONNECTION_STRING

2. Install required packages and launch the backend service:
   ```
   pip3 install -r requirements.txt
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```