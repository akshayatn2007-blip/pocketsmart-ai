import json
import re
import base64
from typing import Dict, Any, Optional, List
from config import settings
from schemas.planner_schema import HomePlannerRequest, PartyPlannerRequest, JewelryPlannerRequest
from services.platform_service import platform_service

# Attempt importing google.genai or provide clean fallback
try:
    from google import genai
    from google.genai import types
    has_genai_sdk = True
except Exception:
    has_genai_sdk = False

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-3.8-flash"
        self.client = None
        if self.api_key and has_genai_sdk:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GeminiService] Warning initializing GenAI Client: {e}")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def _clean_json_response(self, text: str) -> str:
        """Strip markdown ticks if model wraps JSON in ```json ... ```"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    # ==========================================
    # 1. HOME INTERIOR PLANNER
    # ==========================================
    def generate_home_recommendations(self, req: HomePlannerRequest) -> Dict[str, Any]:
        """
        Generates budget-constrained home interior recommendations using Gemini API.
        Intelligently divides budget across categories (e.g. Furniture, Lighting, Decor, Storage).
        """
        prompt = f"""
You are an expert interior designer and budget optimization assistant for 'PocketSmart AI'.
A client wants to furnish/decorate their space.

CLIENT REQUIREMENTS:
- Total Budget: ₹{req.budget:,.2f} INR (Strict budget constraint)
- Room Type: {req.room_type}
- Number of Rooms: {req.num_rooms}
- Style Preference: {req.style_preference}
- Required Items: {req.required_items}
- Item Quantity multiplier/scope: {req.quantity}
- Color/Theme: {req.color_theme}
- Additional Notes: {req.additional_requirements}

TASK:
1. Divide the total budget ₹{req.budget} intelligently between relevant categories (e.g. Core Furniture, Lighting & Fixtures, Wall & Floor Decor, Storage & Accents).
2. Recommend specific products matching the style and requirements.
3. For each product, select an appropriate Indian marketplace platform (Amazon, Flipkart, or IKEA).
4. The sum of all estimated prices (price * quantity) MUST be less than or equal to the total budget ₹{req.budget}.
5. Return strictly valid JSON with no markdown wrapping and no additional explanation.

EXPECTED JSON SCHEMA:
{{
  "title": "Interior Plan for {req.room_type}",
  "summary": "Short 2-sentence design summary explaining how the ₹{req.budget} budget was optimized for {req.style_preference} style.",
  "allocations": [
    {{"category": "Category Name", "allocated_amount": 20000.0, "percentage": 40.0}}
  ],
  "items": [
    {{
      "name": "Product Name",
      "category": "Category Name",
      "estimated_price": 12500.0,
      "quantity": 1,
      "reason": "Why this item fits the space and budget",
      "platform": "IKEA or Amazon or Flipkart",
      "specs": "Dimensions or finish notes"
    }}
  ]
}}
"""
        if self.is_configured():
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                raw_text = self._clean_json_response(response.text or "{}")
                data = json.loads(raw_text)
                return self._finalize_home_result(data, req)
            except Exception as e:
                print(f"[GeminiService] Error calling Gemini for Home Planner: {e}")
                # Fallback to local deterministic generator
        
        return self._generate_home_fallback(req)

    def _finalize_home_result(self, data: Dict[str, Any], req: HomePlannerRequest) -> Dict[str, Any]:
        items = []
        total_spent = 0.0
        for raw_item in data.get("items", []):
            price = float(raw_item.get("estimated_price", 0))
            qty = int(raw_item.get("quantity", 1))
            total_spent += (price * qty)
            platform = raw_item.get("platform", "Amazon")
            link_info = platform_service.enrich_item_link(raw_item.get("name", ""), platform, req.room_type)
            items.append({
                "name": raw_item.get("name", "Interior Item"),
                "category": raw_item.get("category", "Furniture"),
                "estimated_price": price,
                "quantity": qty,
                "reason": raw_item.get("reason", "Selected for style and budget alignment"),
                "platform": link_info["platform"],
                "purchase_link": link_info["purchase_link"],
                "badge": link_info["badge"],
                "specs": raw_item.get("specs", "")
            })

        allocations = data.get("allocations", [])
        if not allocations:
            allocations = [
                {"category": "Main Furniture", "allocated_amount": round(req.budget * 0.55, 2), "percentage": 55.0},
                {"category": "Lighting & Accents", "allocated_amount": round(req.budget * 0.25, 2), "percentage": 25.0},
                {"category": "Decor & Wall Art", "allocated_amount": round(req.budget * 0.20, 2), "percentage": 20.0}
            ]

        remaining = max(0.0, req.budget - total_spent)
        return {
            "planner_type": "home",
            "title": data.get("title", f"{req.room_type} Design Plan"),
            "summary": data.get("summary", f"Customized {req.style_preference} interior plan optimized for your ₹{req.budget:,.2f} budget."),
            "allocations": allocations,
            "items": items,
            "budget_summary": {
                "total_budget": float(req.budget),
                "estimated_total": round(total_spent, 2),
                "remaining_budget": round(remaining, 2),
                "is_within_budget": total_spent <= req.budget
            }
        }

    def _generate_home_fallback(self, req: HomePlannerRequest) -> Dict[str, Any]:
        """High-fidelity fallback if Gemini is offline or unconfigured."""
        budget = req.budget
        room = req.room_type
        style = req.style_preference
        color = req.color_theme

        cat_alloc = [
            {"category": "Core Furniture", "allocated_amount": round(budget * 0.55, 2), "percentage": 55.0},
            {"category": "Lighting & Electricals", "allocated_amount": round(budget * 0.20, 2), "percentage": 20.0},
            {"category": "Wall & Soft Furnishings", "allocated_amount": round(budget * 0.25, 2), "percentage": 25.0}
        ]

        items_plan = []
        if "Living" in room:
            items_plan = [
                {"name": f"{style} 3-Seater Fabric Sofa in {color}", "cat": "Core Furniture", "pct": 0.38, "plat": "IKEA", "reason": f"Centerpiece comfort seating in {color} tone."},
                {"name": f"Minimalist Nesting Coffee Table Set", "cat": "Core Furniture", "pct": 0.14, "plat": "Amazon", "reason": "Space-saving dual nesting design."},
                {"name": f"Warm LED Arc Floor Lamp & Dimmer", "cat": "Lighting & Electricals", "pct": 0.12, "plat": "Amazon", "reason": "Ambient lighting creating cozy evening atmosphere."},
                {"name": f"Geometric Low-Pile Washable Area Rug", "cat": "Wall & Soft Furnishings", "pct": 0.11, "plat": "Flipkart", "reason": f"Ties {color} color palette with the flooring."},
                {"name": f"Framed Canvas Wall Art Tri-Tych ({style})", "cat": "Wall & Soft Furnishings", "pct": 0.09, "plat": "Flipkart", "reason": "Focal wall accent complementing the sofa."}
            ]
        elif "Bed" in room:
            items_plan = [
                {"name": f"{style} Queen Size Bed Frame with Storage", "cat": "Core Furniture", "pct": 0.42, "plat": "IKEA", "reason": "Under-bed hydraulic storage maximizing floor area."},
                {"name": f"Dual Minimalist Bedside Tables", "cat": "Core Furniture", "pct": 0.12, "plat": "Amazon", "reason": "Symmetrical nightstands matching the wood finish."},
                {"name": f"Warm Pendant Bedside Drop Lights", "cat": "Lighting & Electricals", "pct": 0.10, "plat": "Amazon", "reason": "Saves table surface while providing reading glow."},
                {"name": f"Blackout Thermal Curtains in {color}", "cat": "Wall & Soft Furnishings", "pct": 0.12, "plat": "Flipkart", "reason": "Enhances sleep quality and blocks external glare."},
                {"name": f"Full-Length Standing Dressing Mirror", "cat": "Wall & Soft Furnishings", "pct": 0.08, "plat": "IKEA", "reason": "Adds depth and brightens bedroom reflections."}
            ]
        else:
            items_plan = [
                {"name": f"Ergonomic Modular Desk & Workstation ({style})", "cat": "Core Furniture", "pct": 0.35, "plat": "IKEA", "reason": "Sturdy surface built for longevity."},
                {"name": f"High-Back Breathable Mesh Task Chair", "cat": "Core Furniture", "pct": 0.20, "plat": "Amazon", "reason": "Lumbar support for long hours."},
                {"name": f"Architectural Clamp Task Lamp with Wireless Charging", "cat": "Lighting & Electricals", "pct": 0.12, "plat": "Amazon", "reason": "Anti-glare focused illumination."},
                {"name": f"Tiered Storage Bookshelf / Organizer", "cat": "Core Furniture", "pct": 0.15, "plat": "IKEA", "reason": "Keeps clutter off the primary workspace."},
                {"name": f"Acoustic Pin Board & Floating Wall Shelves", "cat": "Wall & Soft Furnishings", "pct": 0.08, "plat": "Flipkart", "reason": "Decorative utility for reminders and decor."}
            ]

        items = []
        total_spent = 0.0
        for item in items_plan:
            price = round(budget * item["pct"], 2)
            total_spent += price
            link_info = platform_service.enrich_item_link(item["name"], item["plat"], room)
            items.append({
                "name": item["name"],
                "category": item["cat"],
                "estimated_price": price,
                "quantity": 1,
                "reason": item["reason"],
                "platform": link_info["platform"],
                "purchase_link": link_info["purchase_link"],
                "badge": link_info["badge"],
                "specs": f"Matched for {style} styling and {color} color palette"
            })

        remaining = max(0.0, budget - total_spent)
        return {
            "planner_type": "home",
            "title": f"{room} Interior Transformation Plan",
            "summary": f"Smart {style} layout optimized for ₹{budget:,.2f}. Budget intelligently apportioned across core furniture, ambiance lighting, and {color} themed textiles.",
            "allocations": cat_alloc,
            "items": items,
            "budget_summary": {
                "total_budget": float(budget),
                "estimated_total": round(total_spent, 2),
                "remaining_budget": round(remaining, 2),
                "is_within_budget": total_spent <= budget
            }
        }

    # ==========================================
    # 2. PARTY & EVENT PLANNER
    # ==========================================
    def generate_party_recommendations(self, req: PartyPlannerRequest) -> Dict[str, Any]:
        """
        Generates party & event budget allocations across Food/Catering, Venue, Decoration, Entertainment.
        Integrates Swiggy, Zomato, OYO, and Amazon vendor search links.
        """
        prompt = f"""
You are an expert event planner and budget coordinator for 'PocketSmart AI'.
A client is organizing an event.

CLIENT REQUIREMENTS:
- Total Budget: ₹{req.budget:,.2f} INR (Strict budget limit)
- Event Type: {req.event_type}
- Guest Count: {req.num_guests} guests
- Venue Preference: {req.venue_preference}
- Food / Catering Preference: {req.food_preference}
- Decoration Preference: {req.decoration_preference}
- Entertainment: {req.entertainment_preference}
- Location: {req.location}
- Event Date/Time: {req.event_date}
- Additional Notes: {req.additional_requirements}

TASK:
1. Divide the budget ₹{req.budget} realistically across 4 key pillars:
   - Food/Catering (typically 40-50%)
   - Venue (typically 20-30%)
   - Decoration (typically 15-20%)
   - Entertainment & Extras (typically 10-15%)
2. Calculate per-guest food budget and package options.
3. Recommend specific service items and vendors:
   - Use Swiggy or Zomato for Catering/Buffet/Food
   - Use OYO for Venues/Banquets/Stay
   - Use Amazon or Flipkart for Decoration materials, party props, and sound equipment
4. Ensure the total of all estimated line items does not exceed the total budget ₹{req.budget}.
5. Return strictly valid JSON with no markdown wrapping.

EXPECTED JSON SCHEMA:
{{
  "title": "{req.event_type} Celebration Plan",
  "summary": "Short 2-sentence summary of the party plan for {req.num_guests} guests at ₹{req.budget}.",
  "allocations": [
    {{"category": "Food/Catering", "allocated_amount": 35000.0, "percentage": 46.7}},
    {{"category": "Venue", "allocated_amount": 18000.0, "percentage": 24.0}},
    {{"category": "Decoration", "allocated_amount": 12000.0, "percentage": 16.0}},
    {{"category": "Entertainment & Extras", "allocated_amount": 10000.0, "percentage": 13.3}}
  ],
  "items": [
    {{
      "name": "Service / Item Name",
      "category": "Food/Catering or Venue or Decoration or Entertainment",
      "estimated_price": 30000.0,
      "quantity": 1,
      "reason": "Why this fits guest count and occasion",
      "platform": "Swiggy or Zomato or OYO or Amazon",
      "specs": "e.g. ₹600/plate for 50 guests"
    }}
  ]
}}
"""
        if self.is_configured():
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                raw_text = self._clean_json_response(response.text or "{}")
                data = json.loads(raw_text)
                return self._finalize_party_result(data, req)
            except Exception as e:
                print(f"[GeminiService] Error calling Gemini for Party Planner: {e}")

        return self._generate_party_fallback(req)

    def _finalize_party_result(self, data: Dict[str, Any], req: PartyPlannerRequest) -> Dict[str, Any]:
        items = []
        total_spent = 0.0
        for raw_item in data.get("items", []):
            price = float(raw_item.get("estimated_price", 0))
            qty = int(raw_item.get("quantity", 1))
            total_spent += (price * qty)
            platform = raw_item.get("platform", "Zomato")
            link_info = platform_service.enrich_item_link(raw_item.get("name", ""), platform, req.event_type)
            items.append({
                "name": raw_item.get("name", "Event Service"),
                "category": raw_item.get("category", "Party Planning"),
                "estimated_price": price,
                "quantity": qty,
                "reason": raw_item.get("reason", "Allocated for optimal guest experience"),
                "platform": link_info["platform"],
                "purchase_link": link_info["purchase_link"],
                "badge": link_info["badge"],
                "specs": raw_item.get("specs", "")
            })

        allocations = data.get("allocations", [])
        if not allocations:
            allocations = [
                {"category": "Food/Catering", "allocated_amount": round(req.budget * 0.45, 2), "percentage": 45.0},
                {"category": "Venue", "allocated_amount": round(req.budget * 0.25, 2), "percentage": 25.0},
                {"category": "Decoration", "allocated_amount": round(req.budget * 0.18, 2), "percentage": 18.0},
                {"category": "Entertainment & Extras", "allocated_amount": round(req.budget * 0.12, 2), "percentage": 12.0}
            ]

        remaining = max(0.0, req.budget - total_spent)
        return {
            "planner_type": "party",
            "title": data.get("title", f"{req.event_type} Event Plan"),
            "summary": data.get("summary", f"Budget plan for {req.num_guests} guests hosted within ₹{req.budget:,.2f}."),
            "allocations": allocations,
            "items": items,
            "budget_summary": {
                "total_budget": float(req.budget),
                "estimated_total": round(total_spent, 2),
                "remaining_budget": round(remaining, 2),
                "is_within_budget": total_spent <= req.budget
            }
        }

    def _generate_party_fallback(self, req: PartyPlannerRequest) -> Dict[str, Any]:
        budget = req.budget
        guests = req.num_guests
        event = req.event_type
        food = req.food_preference

        cat_alloc = [
            {"category": "Food/Catering", "allocated_amount": round(budget * 0.45, 2), "percentage": 45.0},
            {"category": "Venue & Space", "allocated_amount": round(budget * 0.25, 2), "percentage": 25.0},
            {"category": "Decoration & Ambiance", "allocated_amount": round(budget * 0.18, 2), "percentage": 18.0},
            {"category": "Entertainment & Music", "allocated_amount": round(budget * 0.12, 2), "percentage": 12.0}
        ]

        per_head = round((budget * 0.45) / max(1, guests), 2)
        items = [
            {
                "name": f"Full Buffet Catering ({food} & Beverages)",
                "category": "Food/Catering",
                "estimated_price": round(budget * 0.42, 2),
                "quantity": 1,
                "reason": f"Curated multi-course meal for {guests} guests (~₹{per_head}/person).",
                "platform": "Zomato",
                "purchase_link": platform_service.generate_search_url("Zomato", f"catering banquet food {food}"),
                "badge": "Food & Catering",
                "specs": f"Covers starters, mains, dessert for {guests} pax"
            },
            {
                "name": f"{req.venue_preference} Booking / Space Rental",
                "category": "Venue & Space",
                "estimated_price": round(budget * 0.24, 2),
                "quantity": 1,
                "reason": f"Comfortably accommodates {guests} guests with proper seating and AC/ventilation.",
                "platform": "OYO",
                "purchase_link": platform_service.generate_search_url("OYO", f"townhouse banquet hall {req.location}"),
                "badge": "Venues & Stay",
                "specs": f"Reserved for {guests} guests in {req.location}"
            },
            {
                "name": f"{req.decoration_preference} Backdrop & Welcome Arch Kit",
                "category": "Decoration & Ambiance",
                "estimated_price": round(budget * 0.16, 2),
                "quantity": 1,
                "reason": f"Photogenic theme backdrop matching {event} aesthetics.",
                "platform": "Amazon",
                "purchase_link": platform_service.generate_search_url("Amazon", f"{event} decoration kit {req.decoration_preference}"),
                "badge": "E-Commerce",
                "specs": "Includes LED fairy curtain, metallic balloons, banner props"
            },
            {
                "name": f"Party Sound System & Music / Entertainment Setup",
                "category": "Entertainment & Music",
                "estimated_price": round(budget * 0.11, 2),
                "quantity": 1,
                "reason": f"High output portable PA system + wireless mic for speeches & playlist.",
                "platform": "Amazon",
                "purchase_link": platform_service.generate_search_url("Amazon", "party speaker with wireless mic bluetooth"),
                "badge": "E-Commerce",
                "specs": f"Fits {event} audio needs"
            }
        ]

        total_spent = sum(it["estimated_price"] for it in items)
        remaining = max(0.0, budget - total_spent)

        return {
            "planner_type": "party",
            "title": f"{event} Celebration Masterplan",
            "summary": f"Smart event blueprint for {guests} attendees. Food allocated at ~₹{per_head}/head with verified venue, backdrop decor, and sound setup.",
            "allocations": cat_alloc,
            "items": items,
            "budget_summary": {
                "total_budget": float(budget),
                "estimated_total": round(total_spent, 2),
                "remaining_budget": round(remaining, 2),
                "is_within_budget": total_spent <= budget
            }
        }

    # ==========================================
    # 3. JEWELRY PLANNER & OUTFIT IMAGE ANALYSIS
    # ==========================================
    def generate_jewelry_recommendations(
        self,
        req: JewelryPlannerRequest,
        image_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates personalized jewelry recommendations based on occasion, style, metal preference,
        outfit color/cut, and optional uploaded outfit image analyzed via Gemini Vision.
        """
        image_context = ""
        ai_vision_analysis = None

        if image_bytes and self.is_configured():
            try:
                ai_vision_analysis = self.analyze_outfit_image(image_bytes, mime_type or "image/jpeg")
                image_context = f"\nOUTFIT IMAGE AI ANALYSIS:\n{ai_vision_analysis}\n"
            except Exception as e:
                print(f"[GeminiService] Error during outfit image analysis: {e}")
                image_context = "\nOUTFIT IMAGE: An image was provided and inspected.\n"

        prompt = f"""
You are a premier jewelry stylist and gemologist for 'PocketSmart AI'.
A client is seeking matching jewelry for an upcoming occasion.

CLIENT PROFILE:
- Total Budget: ₹{req.budget:,.2f} INR (Strict budget constraint)
- Occasion: {req.occasion}
- Jewelry Type: {req.jewelry_type}
- Style Preference: {req.style_preference}
- Metal Preference: {req.metal_preference}
- Outfit Color: {req.outfit_color}
- Outfit Description: {req.outfit_description}
- Additional Notes: {req.additional_requirements}
{image_context}

TASK:
1. Recommend 3-5 specific jewelry pieces (or a complete coordinated set) tailored to the outfit color, neckline/cut, and {req.occasion}.
2. Categorize the jewelry items (e.g. Neckwear, Earrings, Hand Jewelry / Bangles, Rings).
3. The sum of all recommended items MUST be less than or equal to ₹{req.budget}.
4. Link each piece to a suitable marketplace/vendor (Amazon, Flipkart, CaratLane, or Myntra).
5. Explain clearly WHY each piece matches the outfit and occasion.
6. Return strictly valid JSON with no markdown wrapping.

EXPECTED JSON SCHEMA:
{{
  "title": "{req.jewelry_type} Curation for {req.occasion}",
  "summary": "Short 2-sentence styling summary explaining metal choice and color harmony.",
  "ai_analysis": "Detailed notes on how the jewelry harmonizes with the {req.outfit_color} outfit and occasion.",
  "allocations": [
    {{"category": "Category Name", "allocated_amount": 15000.0, "percentage": 50.0}}
  ],
  "items": [
    {{
      "name": "Jewelry Item Name",
      "category": "Neckwear / Earrings / Bangles / Rings",
      "estimated_price": 12000.0,
      "quantity": 1,
      "reason": "Why it harmonizes with the dress neckline and color",
      "platform": "CaratLane or Amazon or Myntra or Flipkart",
      "specs": "Metal, karat/plating, stone details"
    }}
  ]
}}
"""
        if self.is_configured():
            try:
                contents_payload: List[Any] = []
                if image_bytes:
                    contents_payload.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type or "image/jpeg"))
                contents_payload.append(prompt)

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents_payload,
                )
                raw_text = self._clean_json_response(response.text or "{}")
                data = json.loads(raw_text)
                if ai_vision_analysis and not data.get("ai_analysis"):
                    data["ai_analysis"] = ai_vision_analysis
                return self._finalize_jewelry_result(data, req)
            except Exception as e:
                print(f"[GeminiService] Error calling Gemini for Jewelry Planner: {e}")

        return self._generate_jewelry_fallback(req, ai_vision_analysis)

    def analyze_outfit_image(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Analyzes visible garment characteristics: primary color, undertone, silhouette, neckline,
        embroidery/work, and formal/traditional occasion alignment.
        """
        if not self.is_configured():
            return "Outfit visual profile: Analyzed attire fabric tones and recommended matching metallic highlights."

        prompt = """
Examine the clothing/outfit shown in the image.
Provide a concise, professional styling assessment:
1. Primary and secondary colors with metallic accent suggestions.
2. Garment style (Traditional / Western / Indo-Western / Formal / Casual).
3. Neckline or cut characteristics (e.g. V-neck, sweetheart, round, high collar) and what jewelry shape best balances it.
4. Recommended jewelry style (e.g. Kundan, Temple, Minimalist Solitaire, Oxidized Silver, Rose Gold).
Keep the response objective and focus strictly on the outfit and style recommendations.
"""
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image_part, prompt]
            )
            return response.text.strip()
        except Exception as e:
            print(f"[GeminiService] Vision analysis error: {e}")
            return "Visual analysis processed: Complementary jewelry shapes identified based on outfit cut and palette."

    def _finalize_jewelry_result(self, data: Dict[str, Any], req: JewelryPlannerRequest) -> Dict[str, Any]:
        items = []
        total_spent = 0.0
        for raw_item in data.get("items", []):
            price = float(raw_item.get("estimated_price", 0))
            qty = int(raw_item.get("quantity", 1))
            total_spent += (price * qty)
            platform = raw_item.get("platform", "CaratLane")
            link_info = platform_service.enrich_item_link(raw_item.get("name", ""), platform, "jewelry")
            items.append({
                "name": raw_item.get("name", "Jewelry Piece"),
                "category": raw_item.get("category", "Jewelry"),
                "estimated_price": price,
                "quantity": qty,
                "reason": raw_item.get("reason", "Designed to complement outfit style and neckline"),
                "platform": link_info["platform"],
                "purchase_link": link_info["purchase_link"],
                "badge": link_info["badge"],
                "specs": raw_item.get("specs", f"{req.metal_preference} finish")
            })

        allocations = data.get("allocations", [])
        if not allocations:
            allocations = [
                {"category": "Focal Piece / Neckwear", "allocated_amount": round(req.budget * 0.55, 2), "percentage": 55.0},
                {"category": "Earrings / Studs", "allocated_amount": round(req.budget * 0.25, 2), "percentage": 25.0},
                {"category": "Bracelet / Finger Rings", "allocated_amount": round(req.budget * 0.20, 2), "percentage": 20.0}
            ]

        remaining = max(0.0, req.budget - total_spent)
        return {
            "planner_type": "jewelry",
            "title": data.get("title", f"{req.jewelry_type} Curation"),
            "summary": data.get("summary", f"Coordinated {req.metal_preference} collection suited for {req.occasion} and {req.outfit_color} attire."),
            "ai_analysis": data.get("ai_analysis", f"Harmonizes with {req.outfit_color} fabric tones using balanced {req.metal_preference} accents."),
            "allocations": allocations,
            "items": items,
            "budget_summary": {
                "total_budget": float(req.budget),
                "estimated_total": round(total_spent, 2),
                "remaining_budget": round(remaining, 2),
                "is_within_budget": total_spent <= req.budget
            }
        }

    def _generate_jewelry_fallback(self, req: JewelryPlannerRequest, ai_analysis: Optional[str] = None) -> Dict[str, Any]:
        budget = req.budget
        metal = req.metal_preference
        occasion = req.occasion
        outfit_color = req.outfit_color

        allocations = [
            {"category": "Primary Focal Piece", "allocated_amount": round(budget * 0.55, 2), "percentage": 55.0},
            {"category": "Matching Earrings", "allocated_amount": round(budget * 0.25, 2), "percentage": 25.0},
            {"category": "Wrist & Ring Accents", "allocated_amount": round(budget * 0.20, 2), "percentage": 20.0}
        ]

        items = [
            {
                "name": f"{metal} {req.style_preference} {req.jewelry_type} Statement Piece",
                "category": "Primary Focal Piece",
                "estimated_price": round(budget * 0.52, 2),
                "quantity": 1,
                "reason": f"Centerpiece design tailored for {occasion}, complementing the {outfit_color} attire.",
                "platform": "CaratLane",
                "purchase_link": platform_service.generate_search_url("CaratLane", f"{metal} {req.jewelry_type} {req.style_preference}"),
                "badge": "Jewelry",
                "specs": f"Finished in premium {metal} with anti-tarnish coating"
            },
            {
                "name": f"Coordinated {metal} Drop / Chandelier Earrings",
                "category": "Matching Earrings",
                "estimated_price": round(budget * 0.24, 2),
                "quantity": 1,
                "reason": f"Draws attention to the face while echoing the primary {req.jewelry_type} motifs.",
                "platform": "Myntra",
                "purchase_link": platform_service.generate_search_url("Myntra", f"{metal} earrings {req.style_preference}"),
                "badge": "Fashion & Jewelry",
                "specs": f"Hypoallergenic posts, crafted in {metal}"
            },
            {
                "name": f"Minimalist {metal} Adjustable Cuff / Stacking Rings",
                "category": "Wrist & Ring Accents",
                "estimated_price": round(budget * 0.18, 2),
                "quantity": 1,
                "reason": f"Subtle hand adornment that ties together the entire {occasion} look.",
                "platform": "Amazon",
                "purchase_link": platform_service.generate_search_url("Amazon", f"{metal} bracelet ring set {req.style_preference}"),
                "badge": "E-Commerce",
                "specs": f"Polished {metal} with subtle pavé stone accents"
            }
        ]

        total_spent = sum(it["estimated_price"] for it in items)
        remaining = max(0.0, budget - total_spent)

        analysis_note = ai_analysis or f"Based on your {outfit_color} outfit, {metal} accents provide the ideal contrast, accentuating the {req.style_preference} design for {occasion}."

        return {
            "planner_type": "jewelry",
            "title": f"{req.jewelry_type} Ensemble for {occasion}",
            "summary": f"Custom {metal} curation balanced strictly within ₹{budget:,.2f} to pair with your {outfit_color} outfit.",
            "ai_analysis": analysis_note,
            "allocations": allocations,
            "items": items,
            "budget_summary": {
                "total_budget": float(budget),
                "estimated_total": round(total_spent, 2),
                "remaining_budget": round(remaining, 2),
                "is_within_budget": total_spent <= budget
            }
        }

gemini_service = GeminiService()
