from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user_optional
from services.recommendation_service import recommendation_service

router = APIRouter(tags=["History"])
templates = Jinja2Templates(directory="templates")

@router.get("/history")
def history_endpoint(
    request: Request,
    format: str = "",
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    history_records = recommendation_service.get_user_history(db=db, user=user)

    # Return JSON if requested
    accept_header = request.headers.get("accept", "")
    if format == "json" or "application/json" in accept_header:
        return JSONResponse(content={"records": history_records, "total": len(history_records)})

    return templates.TemplateResponse("history.html", {
        "request": request,
        "user": user,
        "records": history_records,
        "title": "My Planning History - PocketSmart AI"
    })
