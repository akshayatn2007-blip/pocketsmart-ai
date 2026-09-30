import os
import uuid
import base64
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from auth import get_current_user_optional
from schemas.planner_schema import JewelryPlannerRequest
from services.gemini_service import gemini_service
from services.recommendation_service import recommendation_service

router = APIRouter(tags=["Jewelry Planner"])
templates = Jinja2Templates(directory="templates")

@router.get("/jewelry-planner", response_class=HTMLResponse)
def jewelry_planner_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    return templates.TemplateResponse("jewelry_planner.html", {
        "request": request,
        "user": user,
        "title": "Jewelry Planner - PocketSmart AI"
    })

@router.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    content_type = request.headers.get("content-type", "")

    image_bytes = None
    mime_type = "image/jpeg"
    image_filename = None

    if "application/json" in content_type:
        data = await request.json()
        req = JewelryPlannerRequest(**data)
        is_json = True
        if req.image_data:
            # Handle base64 payload
            try:
                if "," in req.image_data:
                    header, b64data = req.image_data.split(",", 1)
                    if "image/png" in header:
                        mime_type = "image/png"
                    elif "image/webp" in header:
                        mime_type = "image/webp"
                else:
                    b64data = req.image_data
                image_bytes = base64.b64decode(b64data)
            except Exception as e:
                print(f"[JewelryRoutes] Error decoding base64 image: {e}")
    else:
        # Multipart form data
        form = await request.form()
        try:
            req = JewelryPlannerRequest(
                budget=float(form.get("budget", 0)),
                occasion=form.get("occasion", "Party"),
                jewelry_type=form.get("jewelry_type", "Complete Set"),
                style_preference=form.get("style_preference", "Contemporary"),
                metal_preference=form.get("metal_preference", "Gold"),
                outfit_color=form.get("outfit_color", "Emerald Green"),
                outfit_description=form.get("outfit_description", ""),
                additional_requirements=form.get("additional_requirements", "")
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid jewelry form parameters: {str(e)}")

        is_json = False
        outfit_file: UploadFile = form.get("outfit_image")
        if outfit_file and hasattr(outfit_file, "filename") and outfit_file.filename:
            # Validate mime type
            file_type = outfit_file.content_type
            if file_type not in settings.ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image type ({file_type}). Supported formats: JPG, JPEG, PNG, WEBP."
                )
            
            image_bytes = await outfit_file.read()
            # Validate size (5MB max)
            if len(image_bytes) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image too large. Maximum allowed file size is {settings.MAX_IMAGE_SIZE_MB}MB."
                )
            mime_type = file_type
            # Save file to uploads folder
            ext = os.path.splitext(outfit_file.filename)[1]
            safe_name = f"outfit_{uuid.uuid4().hex[:10]}{ext}"
            save_path = settings.UPLOAD_DIR / safe_name
            with open(save_path, "wb") as f:
                f.write(image_bytes)
            image_filename = safe_name

    if req.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than zero.")

    rec_result = gemini_service.generate_jewelry_recommendations(
        req=req,
        image_bytes=image_bytes,
        mime_type=mime_type
    )

    req_dict = req.model_dump()
    if image_filename:
        req_dict["image_filename"] = image_filename

    saved_rec = recommendation_service.save_recommendation(
        db=db,
        planner_type="jewelry",
        budget=req.budget,
        request_data=req_dict,
        response_data=rec_result,
        user=user
    )
    rec_result["recommendation_id"] = saved_rec.id

    if is_json or "text/html" not in request.headers.get("accept", ""):
        return JSONResponse(content=rec_result)

    return templates.TemplateResponse("jewelry_recommendations.html", {
        "request": request,
        "user": user,
        "plan": rec_result,
        "req_data": req_dict
    })

@router.get("/jewelry-recommendations", response_class=HTMLResponse)
def jewelry_recommendations_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    rec = recommendation_service.get_recommendation_details(db=db, planner_type="jewelry")
    return templates.TemplateResponse("jewelry_recommendations.html", {
        "request": request,
        "user": user,
        "plan": rec.get("response_data", {}),
        "req_data": rec.get("request_data", {})
    })
