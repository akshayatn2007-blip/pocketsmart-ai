from typing import Optional, List
from pydantic import BaseModel, Field

class HomePlannerRequest(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    room_type: str = Field(..., description="e.g., Living Room, Bedroom, Kitchen, Dining Room, Office")
    num_rooms: int = Field(default=1, ge=1, description="Number of rooms to furnish/decorate")
    style_preference: str = Field(..., description="e.g., Modern, Minimalist, Scandinavian, Traditional, Bohemian, Industrial")
    required_items: str = Field(..., description="Comma separated or descriptive list of required furniture/decor items")
    quantity: int = Field(default=1, ge=1, description="General item quantity multiplier or estimated piece count")
    color_theme: str = Field(..., description="Preferred color palette or theme")
    additional_requirements: Optional[str] = Field(default="", description="Special notes or constraints")

class PartyPlannerRequest(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    event_type: str = Field(..., description="Birthday, Wedding, Corporate, Anniversary, College Event, Other")
    num_guests: int = Field(..., ge=1, description="Expected number of attendees")
    venue_preference: str = Field(..., description="Indoor Hall, Outdoor Lawn, Banquet, Home, Rooftop, etc.")
    food_preference: str = Field(..., description="Vegetarian, Non-Vegetarian, Buffet, Multi-Cuisine, Snacks & Mocktails")
    decoration_preference: str = Field(..., description="Floral, Minimalist, Themed, Fairy Lights, Balloons, Luxury")
    entertainment_preference: str = Field(default="Music & DJ", description="DJ, Live Acoustic, Games, Emcee, Photobooth")
    location: str = Field(default="Local City", description="City / area")
    event_date: Optional[str] = Field(default="", description="Event date or timeframe")
    additional_requirements: Optional[str] = Field(default="", description="Specific preferences or allergies")

class JewelryPlannerRequest(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    occasion: str = Field(..., description="Wedding, Engagement, Birthday, Party, Traditional Event, Office Event, Other")
    jewelry_type: str = Field(..., description="Necklace, Earrings, Ring, Bracelet, Complete Bridal Set, Bangles")
    style_preference: str = Field(..., description="Traditional, Minimalist, Contemporary, Royal/Antique, Statement")
    metal_preference: str = Field(..., description="Gold, Silver, Diamond, Platinum, Rose Gold, Artificial/Oxidized")
    outfit_color: str = Field(..., description="Color of the dress/attire")
    outfit_description: str = Field(default="", description="Description of neckline, embroidery, fabric, or cut")
    additional_requirements: Optional[str] = Field(default="", description="Skin tone suitability, weight preference, etc.")
    image_data: Optional[str] = Field(default=None, description="Optional Base64 encoded outfit image")
    image_filename: Optional[str] = Field(default=None, description="Optional uploaded image filename")
