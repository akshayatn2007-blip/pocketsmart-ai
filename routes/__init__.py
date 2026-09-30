from routes.auth_routes import router as auth_router
from routes.home_routes import router as home_router
from routes.party_routes import router as party_router
from routes.jewelry_routes import router as jewelry_router
from routes.recommendation_routes import router as recommendation_router
from routes.history_routes import router as history_router

__all__ = [
    "auth_router",
    "home_router",
    "party_router",
    "jewelry_router",
    "recommendation_router",
    "history_router",
]
