from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user_optional
from services.recommendation_service import recommendation_service

router = APIRouter(tags=["Recommendations"])

@router.get("/recommendations-details")
def get_recommendation_details(
    request: Request,
    planner_type: Optional[str] = Query(None, description="home, party, or jewelry"),
    rec_id: Optional[int] = Query(None, description="Specific recommendation record ID"),
    category: Optional[str] = Query(None, description="Category filter (e.g. Furniture, Catering, Rings)"),
    db: Session = Depends(get_db)
):
    details = recommendation_service.get_recommendation_details(
        db=db,
        planner_type=planner_type,
        rec_id=rec_id,
        category=category
    )
    return JSONResponse(content=details)
