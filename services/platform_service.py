import urllib.parse
from typing import Dict, Any

class PlatformService:
    """
    Platform integration service for e-commerce, food, and hospitality vendors.
    Provides verified search URL generation and vendor metadata abstraction.
    Direct private API hooks can be plugged into this class in production.
    """

    SUPPORTED_PLATFORMS: Dict[str, Dict[str, Any]] = {
        "Amazon": {
            "name": "Amazon India",
            "base_url": "https://www.amazon.in/s?k=",
            "color": "#FF9900",
            "badge": "E-Commerce",
            "categories": ["home", "party", "jewelry"]
        },
        "Flipkart": {
            "name": "Flipkart",
            "base_url": "https://www.flipkart.com/search?q=",
            "color": "#2874F0",
            "badge": "E-Commerce",
            "categories": ["home", "party", "jewelry"]
        },
        "IKEA": {
            "name": "IKEA India",
            "base_url": "https://www.ikea.com/in/en/search/?q=",
            "color": "#0058A3",
            "badge": "Home & Furniture",
            "categories": ["home"]
        },
        "Swiggy": {
            "name": "Swiggy",
            "base_url": "https://www.swiggy.com/search?query=",
            "color": "#FC8019",
            "badge": "Food & Catering",
            "categories": ["party"]
        },
        "Zomato": {
            "name": "Zomato",
            "base_url": "https://www.zomato.com/search?q=",
            "color": "#E23744",
            "badge": "Dining & Events",
            "categories": ["party"]
        },
        "OYO": {
            "name": "OYO Rooms & Venues",
            "base_url": "https://www.oyorooms.com/search?location=",
            "color": "#EE2E24",
            "badge": "Venues & Stay",
            "categories": ["party"]
        },
        "CaratLane": {
            "name": "CaratLane (Tanishq)",
            "base_url": "https://www.caratlane.com/search?q=",
            "color": "#7B1FA2",
            "badge": "Jewelry",
            "categories": ["jewelry"]
        },
        "Myntra": {
            "name": "Myntra Fashion",
            "base_url": "https://www.myntra.com/",
            "color": "#FF3F6C",
            "badge": "Fashion & Jewelry",
            "categories": ["jewelry"]
        }
    }

    @classmethod
    def generate_search_url(cls, platform: str, query: str) -> str:
        """
        Generates a clean, transparent search URL for the specified platform.
        Does not pretend to return real-time internal warehouse data.
        """
        encoded_query = urllib.parse.quote_plus(query.strip())
        platform_info = cls.SUPPORTED_PLATFORMS.get(platform)
        
        if not platform_info:
            # Default to Amazon India search if platform is unrecognized
            return f"https://www.amazon.in/s?k={encoded_query}"
        
        if platform == "Myntra":
            return f"https://www.myntra.com/{encoded_query.replace('+', '-')}"
        
        return f"{platform_info['base_url']}{encoded_query}"

    @classmethod
    def get_platform_info(cls, platform: str) -> Dict[str, Any]:
        return cls.SUPPORTED_PLATFORMS.get(platform, {
            "name": platform,
            "color": "#4F46E5",
            "badge": "Verified Vendor"
        })

    @classmethod
    def enrich_item_link(cls, item_name: str, preferred_platform: str, category_context: str = "") -> Dict[str, str]:
        """
        Takes an item name and preferred platform, generating valid search links and platform metadata.
        """
        search_phrase = f"{item_name} {category_context}".strip()
        url = cls.generate_search_url(preferred_platform, search_phrase)
        info = cls.get_platform_info(preferred_platform)
        return {
            "platform": preferred_platform,
            "purchase_link": url,
            "badge": info.get("badge", "Vendor")
        }

platform_service = PlatformService()
