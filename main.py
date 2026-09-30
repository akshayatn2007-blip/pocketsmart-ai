import os
from pathlib import Path
from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import init_db, get_db
from auth import get_current_user_optional
from models.user import User
from models.recommendation import Recommendation
from routes import (
    auth_router,
    home_router,
    party_router,
    jewelry_router,
    recommendation_router,
    history_router
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files and Uploads
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
uploads_dir = BASE_DIR / "uploads"
templates_dir = BASE_DIR / "templates"

os.makedirs(static_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

templates = Jinja2Templates(directory=str(templates_dir))

# Automatically initialize database schema at startup
@app.on_event("startup")
def on_startup():
    print(f"[{settings.PROJECT_NAME}] Initializing database tables...")
    init_db()
    print(f"[{settings.PROJECT_NAME}] Database ready at {settings.DATABASE_URL}")

# Include Router Modules
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(party_router)
app.include_router(jewelry_router)
app.include_router(recommendation_router)
app.include_router(history_router)

# ==========================================
# CORE PAGES & SYSTEM ENDPOINTS
# ==========================================

@app.get("/startup")
def startup_check():
    """System health check and diagnostic endpoint."""
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected",
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request, db: Session = Depends(get_db)):
    """Landing page introducing PocketSmart AI, features, how it works, testimonials."""
    user = get_current_user_optional(request, db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "title": "PocketSmart AI - Smart Budget & Recommendation Assistant"
    })

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    """User dashboard showing stats, recent plans, and quick planner shortcuts."""
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login?msg=auth_required", status_code=status.HTTP_302_FOUND)

    # Fetch user's recent plans
    recent_plans = db.query(Recommendation).filter(
        Recommendation.user_id == user.id
    ).order_by(Recommendation.created_at.desc()).limit(5).all()

    total_count = db.query(Recommendation).filter(Recommendation.user_id == user.id).count()

    total_budget_planned = sum(p.budget for p in recent_plans)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "recent_plans": recent_plans,
        "total_count": total_count,
        "total_budget_planned": total_budget_planned,
        "title": "Dashboard - PocketSmart AI"
    })

@app.get("/testimonials", response_class=HTMLResponse)
def testimonials_page(request: Request, db: Session = Depends(get_db)):
    """Dedicated testimonials and project demonstration review page."""
    user = get_current_user_optional(request, db)
    return templates.TemplateResponse("testimonials.html", {
        "request": request,
        "user": user,
        "title": "Testimonials & College Demo Reviews - PocketSmart AI"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
