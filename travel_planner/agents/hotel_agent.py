from typing import List, Dict, Any
from travel_planner.tools.scraper import agoda_search

class HotelAgent:
    """
    HotelAgent is specialized: it ONLY queries Agoda via agoda_search().
    """
    def search(self, destination: str, check_in: str, check_out: str, max_price_per_night: float | None=None, stars_preference:int | None=None) -> List[Dict[str,Any]]:
        hotels = agoda_search(destination, check_in, check_out, max_price_per_night, stars_preference)
        return hotels
