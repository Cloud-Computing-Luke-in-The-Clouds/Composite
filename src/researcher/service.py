from sqlalchemy import select
from sqlalchemy.orm import Session
from src.researcher.models import ResearchProfile
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import Optional, Dict, Any

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

def update_research_profile(db: Session, researcher_id: int, research_profile: ResearchProfile, partial: bool = True):
    """
    Update a research profile
    
    Args:
        db: Database session
        researcher_id: ID of the researcher to update
        research_profile: New profile data
        partial: If True, do PATCH (partial update). If False, do PUT (full replacement)
    """
    db_profile = (db.query(ResearchProfile)
                 .filter(ResearchProfile.id == researcher_id)
                 .first())
    
    if not db_profile:
        return None
        
    if partial:
        # PATCH - only update provided fields
        for key, value in research_profile.dict(exclude_unset=True).items():
            setattr(db_profile, key, value)
    else:
        # PUT - update all fields
        profile_data = research_profile.dict()
        for key, value in profile_data.items():
            setattr(db_profile, key, value)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

