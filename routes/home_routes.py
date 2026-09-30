from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user_optional
from schemas.planner_schema import HomePlannerRequest
from services.gemini_service import gemini_service
from services.recommendation_service import recommendation_service

router = APIRouter(tags=["Home Interior Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/home-planner", response_class=HTMLResponse)
def home_planner_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    return templates.TemplateResponse("home_planner.html", {
        "request": request,
        "user": user,
        "title": "Home Interior Planner - PocketSmart AI"
    })

@router.post("/generate-home")
async def generate_home(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            data = await request.json()
            req = HomePlannerRequest(**data)
            is_json = True
        else:
            form = await request.form()
            req = HomePlannerRequest(
                budget=float(form.get("budget", 0)),
                room_type=form.get("room_type", "Living Room"),
                num_rooms=int(form.get("num_rooms", 1)),
                style_preference=form.get("style_preference", "Modern"),
                required_items=form.get("required_items", "Sofa, Coffee Table, Lighting"),
                quantity=int(form.get("quantity", 1)),
                color_theme=form.get("color_theme", "Warm Neutrals"),
                additional_requirements=form.get("additional_requirements", "")
            )
            is_json = False
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid form input: {str(e)}")

    if req.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than zero.")

    # Generate AI recommendations
    rec_result = gemini_service.generate_home_recommendations(req)

    # Save to SQLite database
    saved_rec = recommendation_service.save_recommendation(
        db=db,
        planner_type="home",
        budget=req.budget,
        request_data=req.model_dump(),
        response_data=rec_result,
        user=user
    )
    rec_result["recommendation_id"] = saved_rec.id

    if is_json or "text/html" not in request.headers.get("accept", ""):
        return JSONResponse(content=rec_result)

    return templates.TemplateResponse("home_recommendations.html", {
        "request": request,
        "user": user,
        "plan": rec_result,
        "req_data": req.model_dump()
    })

@router.get("/home-recommendations", response_class=HTMLResponse)
def home_recommendations_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    rec = recommendation_service.get_recommendation_details(db=db, planner_type="home")
    return templates.TemplateResponse("home_recommendations.html", {
        "request": request,
        "user": user,
        "plan": rec.get("response_data", {}),
        "req_data": rec.get("request_data", {})
    })
