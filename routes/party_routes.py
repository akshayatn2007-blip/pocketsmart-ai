from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user_optional
from schemas.planner_schema import PartyPlannerRequest
from services.gemini_service import gemini_service
from services.recommendation_service import recommendation_service

router = APIRouter(tags=["Party & Event Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/party-planner", response_class=HTMLResponse)
def party_planner_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    return templates.TemplateResponse("party_planner.html", {
        "request": request,
        "user": user,
        "title": "Party & Event Planner - PocketSmart AI"
    })

@router.post("/generate-party")
async def generate_party(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            data = await request.json()
            req = PartyPlannerRequest(**data)
            is_json = True
        else:
            form = await request.form()
            req = PartyPlannerRequest(
                budget=float(form.get("budget", 0)),
                event_type=form.get("event_type", "Birthday"),
                num_guests=int(form.get("num_guests", 25)),
                venue_preference=form.get("venue_preference", "Indoor Banquet"),
                food_preference=form.get("food_preference", "Buffet"),
                decoration_preference=form.get("decoration_preference", "Themed & Balloons"),
                entertainment_preference=form.get("entertainment_preference", "Music & DJ"),
                location=form.get("location", "City Center"),
                event_date=form.get("event_date", ""),
                additional_requirements=form.get("additional_requirements", "")
            )
            is_json = False
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid party form input: {str(e)}")

    if req.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than zero.")
    if req.num_guests < 1:
        raise HTTPException(status_code=400, detail="Guest count must be at least 1.")

    rec_result = gemini_service.generate_party_recommendations(req)

    saved_rec = recommendation_service.save_recommendation(
        db=db,
        planner_type="party",
        budget=req.budget,
        request_data=req.model_dump(),
        response_data=rec_result,
        user=user
    )
    rec_result["recommendation_id"] = saved_rec.id

    if is_json or "text/html" not in request.headers.get("accept", ""):
        return JSONResponse(content=rec_result)

    return templates.TemplateResponse("party_recommendations.html", {
        "request": request,
        "user": user,
        "plan": rec_result,
        "req_data": req.model_dump()
    })

@router.get("/party-recommendations", response_class=HTMLResponse)
def party_recommendations_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    rec = recommendation_service.get_recommendation_details(db=db, planner_type="party")
    return templates.TemplateResponse("party_recommendations.html", {
        "request": request,
        "user": user,
        "plan": rec.get("response_data", {}),
        "req_data": rec.get("request_data", {})
    })
