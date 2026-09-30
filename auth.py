from datetime import datetime, timedelta
from typing import Optional
import hashlib
import json
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User

# Try importing passlib / jose; provide safe fallbacks if running in varied python environments
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    pwd_context = None

try:
    from jose import JWTError, jwt
except Exception:
    jwt = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    # Fallback to SHA-256 with salt if passlib is unavailable
    parts = hashed_password.split("$")
    if len(parts) == 3 and parts[0] == "sha256":
        salt = parts[1]
        expected = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return parts[2] == expected
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass
    import secrets
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"sha256${salt}${h}"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    
    if jwt:
        try:
            return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        except Exception:
            pass
    # Lightweight deterministic JWT-style fallback
    import hmac, base64
    payload_str = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode()
    sig = hmac.new(settings.SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    return f"{payload_str}.{sig}"

def decode_access_token(token: str) -> Optional[dict]:
    if not token:
        return None
    if jwt:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except Exception:
            pass
    try:
        import hmac, base64
        parts = token.split(".")
        if len(parts) == 2:
            payload_str, sig = parts
            expected = hmac.new(settings.SECRET_KEY.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
            if hmac.compare_digest(sig, expected):
                data = json.loads(base64.urlsafe_b64decode(payload_str.encode()).decode())
                if data.get("exp") and datetime.utcnow().timestamp() > data["exp"]:
                    return None
                return data
    except Exception:
        return None
    return None

def extract_token_from_request(request: Request) -> Optional[str]:
    # 1. Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    # 2. Check cookies
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token.split(" ")[1]
        return cookie_token
    return None

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    token = extract_token_from_request(request)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        return None
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except Exception:
        return None

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
