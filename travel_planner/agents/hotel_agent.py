from typing import List, Dict, Any
from travel_planner.tools.scraper import agoda_search

class HotelAgent:
    """
    HotelAgent is specialized: it ONLY queries Agoda via agoda_search().
    """
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[HOTEL_AGENT] {message}")
    
    def search(self, destination: str, check_in: str, check_out: str, max_price_per_night: float | None=None, stars_preference:int | None=None) -> List[Dict[str,Any]]:
        self._log(f"Searching hotels in {destination}, {check_in} to {check_out}, Max: ${max_price_per_night}/night, Stars: {stars_preference}")
        hotels = agoda_search(destination, check_in, check_out, max_price_per_night, stars_preference, verbose=self.verbose)
        self._log(f"Found {len(hotels)} hotels")
        return hotels
