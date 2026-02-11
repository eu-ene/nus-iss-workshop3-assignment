from typing import List, Dict, Any
from travel_planner.tools.scraper import tripadvisor_restaurants_search

class RestaurantAgent:
    """
    RestaurantAgent is specialized: it ONLY queries TripAdvisor via tripadvisor_restaurants_search().
    """
    def search(self, destination: str, cuisine: str | None=None, price_level: int | None=None, limit:int=10) -> List[Dict[str,Any]]:
        restaurants = tripadvisor_restaurants_search(destination, cuisine, price_level, limit)
        return restaurants
