from sqlalchemy import select
from sqlalchemy.orm import Session
from src.researcher.models import ResearchProfile
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import Optional, Dict, Any
import time

class ResearcherCompositeService:
    def __init__(self, db: Session):
        self.db = db

    async def get_researcher_composite(
        self,
        researcher_id: int,
        base_profile: Dict[str, Any],
        include_papers: bool = True,
        include_scholar_metrics: bool = True
    ) -> Optional[Dict[str, Any]]:
        try:
            start_time = time.time()
            print(f"Starting async composite fetch at {start_time}")
            
            db_profile = get_research_profile_by_id(self.db, researcher_id)
            if not db_profile:
                return None

            composite_profile = {
                "id": researcher_id,
                "base_profile": base_profile,
                "db_profile": {
                    "google_scholar_link": db_profile.google_scholar_link,
                    "personal_website_link": db_profile.personal_website_link,
                    "organization": db_profile.organization,
                    "title": db_profile.title,
                    "age": db_profile.age,
                    "sex": db_profile.sex
                }
            }

            if include_papers and db_profile.google_scholar_link:
                papers = await self._fetch_papers(db_profile.google_scholar_link)
                composite_profile["papers"] = papers

            if include_scholar_metrics and db_profile.google_scholar_link:
                metrics = await self._fetch_scholar_metrics(db_profile.google_scholar_link)
                composite_profile["scholar_metrics"] = metrics

            end_time = time.time()
            execution_time = end_time - start_time
            composite_profile["execution_info"] = {
                "start_time": start_time,
                "end_time": end_time,
                "execution_time_seconds": execution_time,
                "type": "asynchronous"
            }
            
            print(f"Completed async composite fetch in {execution_time} seconds")
            return composite_profile

        except Exception as e:
            print(f"Error in get_researcher_composite: {str(e)}")
            raise

    def get_researcher_composite_sync(
        self,
        researcher_id: int,
        base_profile: Dict[str, Any],
        include_papers: bool = True,
        include_scholar_metrics: bool = True
    ) -> Optional[Dict[str, Any]]:
        try:
            start_time = time.time()
            print(f"Starting sync composite fetch at {start_time}")
            
            db_profile = get_research_profile_by_id(self.db, researcher_id)
            if not db_profile:
                return None

            composite_profile = {
                "id": researcher_id,
                "base_profile": base_profile,
                "db_profile": {
                    "google_scholar_link": db_profile.google_scholar_link,
                    "personal_website_link": db_profile.personal_website_link,
                    "organization": db_profile.organization,
                    "title": db_profile.title,
                    "age": db_profile.age,
                    "sex": db_profile.sex
                }
            }

            if include_papers and db_profile.google_scholar_link:
                papers = self._fetch_papers_sync(db_profile.google_scholar_link)
                composite_profile["papers"] = papers

            if include_scholar_metrics and db_profile.google_scholar_link:
                metrics = self._fetch_scholar_metrics_sync(db_profile.google_scholar_link)
                composite_profile["scholar_metrics"] = metrics

            end_time = time.time()
            execution_time = end_time - start_time
            composite_profile["execution_info"] = {
                "start_time": start_time,
                "end_time": end_time,
                "execution_time_seconds": execution_time,
                "type": "synchronous"
            }
            
            print(f"Completed sync composite fetch in {execution_time} seconds")
            return composite_profile

        except Exception as e:
            print(f"Error in get_researcher_composite_sync: {str(e)}")
            raise

    async def _fetch_papers(self, scholar_link: str) -> list:
        await asyncio.sleep(2)  # Simulate async API call delay
        return [{"title": "Async Paper 1"}, {"title": "Async Paper 2"}]

    async def _fetch_scholar_metrics(self, scholar_link: str) -> dict:
        await asyncio.sleep(2)  # Simulate async API call delay
        return {
            "citations": 100,
            "h_index": 10,
            "i10_index": 15
        }

    def _fetch_papers_sync(self, scholar_link: str) -> list:
        time.sleep(2)  # Simulate sync API call delay
        return [{"title": "Sync Paper 1"}, {"title": "Sync Paper 2"}]

    def _fetch_scholar_metrics_sync(self, scholar_link: str) -> dict:
        time.sleep(2)  # Simulate sync API call delay
        return {
            "citations": 100,
            "h_index": 10,
            "i10_index": 15
        }

def get_research_profile_by_id(db: Session, researcher_id: int):
    return (db.query(ResearchProfile)
            .filter(ResearchProfile.id == researcher_id).first())


def get_all_research_profiles(db: Session, skip: int = 0, limit: int = 100):
    return paginate(db, select(ResearchProfile).order_by(ResearchProfile.id), additional_data={
            "link": ""
        })


def create_research_profile(db: Session, research_profile: ResearchProfile):
    new_research_profile = ResearchProfile(
       google_scholar_link=research_profile.google_scholar_link,
       personal_website_link=research_profile.personal_website_link,
       organization=research_profile.organization,
       title=research_profile.title,
       age=research_profile.age,
       sex=research_profile.sex
    )
    db.add(new_research_profile)
    db.commit()
    db.refresh(new_research_profile)
    return new_research_profile


def delete_research_profile_by_id(db: Session, researcher_id: int):
    (db.query(ResearchProfile)
        .filter(ResearchProfile.id == researcher_id).delete())
    db.commit()
    return

def update_research_profile(db: Session, researcher_id: int, research_profile: ResearchProfile):
    db_profile = (db.query(ResearchProfile)
                 .filter(ResearchProfile.id == researcher_id)
                 .first())
    
    if not db_profile:
        return None
        
    # Update the profile fields
    for key, value in research_profile.dict(exclude_unset=True).items():
        setattr(db_profile, key, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile