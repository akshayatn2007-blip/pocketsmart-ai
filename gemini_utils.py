"""
gemini_utils.py: Centralized utility module exposing standard recommendation and image analysis functions.
"""
from typing import Optional, Dict, Any
from services.gemini_service import gemini_service
from schemas.planner_schema import HomePlannerRequest, PartyPlannerRequest, JewelryPlannerRequest

def generate_home_recommendations(req: HomePlannerRequest) -> Dict[str, Any]:
    return gemini_service.generate_home_recommendations(req)

def generate_party_recommendations(req: PartyPlannerRequest) -> Dict[str, Any]:
    return gemini_service.generate_party_recommendations(req)

def generate_jewelry_recommendations(
    req: JewelryPlannerRequest,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    return gemini_service.generate_jewelry_recommendations(req, image_bytes=image_bytes, mime_type=mime_type)

def analyze_outfit_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    return gemini_service.analyze_outfit_image(image_bytes, mime_type)
