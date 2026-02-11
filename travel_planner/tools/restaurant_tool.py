import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional, List

# --- Mock Data Store ---
MOCK_RESTAURANTS = {
    "san francisco": [
        {"name": "Zuni Café", "cuisine": "French/Italian", "rating": 4.6, "price_level": "$$$", "neighborhood": "Hayes Valley"},
        {"name": "Sotto Mare", "cuisine": "Seafood", "rating": 4.7, "price_level": "$$", "neighborhood": "North Beach"},
        {"name": "Mister Jiu's", "cuisine": "Modern Chinese", "rating": 4.5, "price_level": "$$$$", "neighborhood": "Chinatown"},
        {"name": "Brenda's French Soul Food", "cuisine": "Creole/Southern", "rating": 4.4, "price_level": "$$", "neighborhood": "Tenderloin"},
        {"name": "La Taqueria", "cuisine": "Mexican", "rating": 4.8, "price_level": "$", "neighborhood": "Mission District"}
    ],
    "tokyo": [
        {"name": "Kaiten Sushi Toriton", "cuisine": "Sushi", "rating": 4.7, "price_level": "$$", "neighborhood": "Sumida"},
        {"name": "Rokurinsha", "cuisine": "Ramen", "rating": 4.5, "price_level": "$", "neighborhood": "Tokyo Station"},
        {"name": "Sézanne", "cuisine": "Modern French", "rating": 4.9, "price_level": "$$$$", "neighborhood": "Marunouchi"},
        {"name": "Gyukatsu Motomura", "cuisine": "Beef Cutlet", "rating": 4.6, "price_level": "$$", "neighborhood": "Shibuya"},
        {"name": "Den", "cuisine": "Kaiseki", "rating": 4.8, "price_level": "$$$$", "neighborhood": "Jingumae"}
    ],
    "london": [
        {"name": "Dishoom", "cuisine": "Indian", "rating": 4.7, "price_level": "$$", "neighborhood": "Soho"},
        {"name": "The Ledbury", "cuisine": "Modern British", "rating": 4.9, "price_level": "$$$$", "neighborhood": "Notting Hill"},
        {"name": "Padella", "cuisine": "Italian", "rating": 4.6, "price_level": "$$", "neighborhood": "Borough Market"},
        {"name": "St. John", "cuisine": "British", "rating": 4.5, "price_level": "$$$", "neighborhood": "Smithfield"},
        {"name": "Tayyabs", "cuisine": "Punjabi", "rating": 4.4, "price_level": "$", "neighborhood": "Whitechapel"}
    ]
}

# --- Tool Input Schema ---
class RestaurantSearchInput(BaseModel):
    location: str = Field(description="The city to search in (e.g., 'London', 'Tokyo', 'San Francisco')")
    cuisine: Optional[str] = Field(default=None, description="The type of food (e.g., 'Italian', 'Sushi')")
    max_price: Optional[str] = Field(default=None, description="Maximum price level ($, $$, $$$, $$$$)")

# --- Tool Definition ---
@tool("search_restaurants", args_schema=RestaurantSearchInput)
def search_restaurants(location: str, cuisine: Optional[str] = None, max_price: Optional[str] = None) -> str:
    """Search for restaurants in a specific city with optional filters for cuisine and price."""
    
    city = location.lower()
    if city not in MOCK_RESTAURANTS:
        return f"I'm sorry, I don't have restaurant data for {location} yet."
    
    results = MOCK_RESTAURANTS[city]
    
    # Filter by cuisine
    if cuisine:
        results = [r for r in results if cuisine.lower() in r["cuisine"].lower()]
        
    # Filter by price (converting '$' signs to length for comparison)
    if max_price:
        max_val = len(max_price)
        results = [r for r in results if len(r["price_level"]) <= max_val]
        
    if not results:
        return f"No restaurants found in {location} matching your specific criteria."

    return json.dumps(results, indent=2)