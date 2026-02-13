from typing import List, Dict, Any
from travel_planner.tools.scraper import mock_restaurants_search

class RestaurantAgent:
    """
    RestaurantAgent is specialized: it ONLY queries mock data via mock_restaurants_search().
    """
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[RESTAURANT_AGENT] {message}")
    
    def search(self, destination: str, cuisine: str | None=None, price_level: int | None=None, limit:int=10) -> List[Dict[str,Any]]:
        self._log(f"Searching restaurants in {destination}, Cuisine: {cuisine}, Limit: {limit}")
        restaurants = mock_restaurants_search(destination, cuisine, price_level, limit)
        self._log(f"Found {len(restaurants)} restaurants")
        return restaurants
