from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User
from schemas.user_schema import UserRegister, UserLogin, UserResponse, Token
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_user_optional,
)

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

# ==========================================
# TEMPLATE PAGES (HTML)
# ==========================================
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "user": None, "error": None})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("register.html", {"request": request, "user": None, "error": None})

# ==========================================
# AUTH API ENDPOINTS
# ==========================================
@router.post("/register")
async def register(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # Support both JSON payload and Form submission
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        name = body.get("name")
        email = body.get("email")
        password = body.get("password")
        confirm_password = body.get("confirm_password")
        is_json = True
    else:
        form = await request.form()
        name = form.get("name")
        email = form.get("email")
        password = form.get("password")
        confirm_password = form.get("confirm_password")
        is_json = False

    # Validation
    if not name or not email or not password:
        err = "All fields are required."
        if is_json:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "error": err, "name": name, "email": email})

    if len(password) < 6:
        err = "Password must be at least 6 characters long."
        if is_json:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "error": err, "name": name, "email": email})

    if password != confirm_password:
        err = "Passwords do not match."
        if is_json:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "error": err, "name": name, "email": email})

    # Check duplicate
    existing = db.query(User).filter(User.email == email.strip().lower()).first()
    if existing:
        err = "An account with this email already exists."
        if is_json:
            raise HTTPException(status_code=400, detail=err)
        return templates.TemplateResponse("register.html", {"request": request, "error": err, "name": name, "email": email})

    hashed = get_password_hash(password)
    new_user = User(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if is_json:
        return {"status": "success", "message": "Registration successful. Please log in.", "user_id": new_user.id}
    
    return RedirectResponse(url="/login?registered=true", status_code=status.HTTP_302_FOUND)

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email", "").strip().lower()
        password = body.get("password", "")
        is_json = True
    else:
        form = await request.form()
        email = form.get("email", "").strip().lower()
        password = form.get("password", "")
        is_json = False

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        err = "Invalid email or password."
        if is_json:
            raise HTTPException(status_code=401, detail=err)
        return templates.TemplateResponse("login.html", {"request": request, "error": err, "email": email})

    token = create_access_token(data={"sub": str(user.id), "user_id": user.id, "email": user.email})

    if is_json:
        res = JSONResponse(content={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            }
        })
        res.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, max_age=86400, samesite="lax")
        return res

    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True, max_age=86400, samesite="lax")
    return redirect

@router.post("/token", response_model=Token)
async def token_endpoint(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username") or form.get("email")
    password = form.get("password")
    user = db.query(User).filter(User.email == (username or "").strip().lower()).first()
    if not user or not verify_password(password or "", user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user.id), "user_id": user.id, "email": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at
        }
    }

@router.get("/logout")
def logout(response: Response):
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie(key="access_token")
    return redirect

@router.get("/session-info")
def session_info(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }
    }

@router.get("/session-data")
def session_data(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    return {
        "logged_in": bool(user),
        "user_id": user.id if user else None,
        "user_name": user.name if user else "Guest",
        "user_email": user.email if user else None
    }
