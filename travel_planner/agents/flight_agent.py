from typing import List, Dict, Any
from travel_planner.tools.scraper import amadeus_flights_search

class FlightAgent:
    """
    FlightAgent is specialized: it ONLY queries Amadeus via amadeus_flights_search() (function name kept for compatibility).
    Returns flights sorted by price.
    """
    def search(self, origin: str, destination: str, depart_date: str, return_date: str | None=None, passengers:int=1, budget: float | None=None) -> List[Dict[str,Any]]:
        flights = amadeus_flights_search(origin, destination, depart_date, return_date, passengers)
        flights_sorted = sorted(flights, key=lambda f: f.get("price", float('inf')))
        if budget:
            affordable = [f for f in flights_sorted if f.get("price", float('inf')) <= budget]
            return affordable if affordable else flights_sorted
        return flights_sorted
