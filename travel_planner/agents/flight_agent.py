from typing import List, Dict, Any
from travel_planner.tools.scraper import amadeus_flights_search

class FlightAgent:
    """
    FlightAgent is specialized: it ONLY queries Amadeus via amadeus_flights_search() (function name kept for compatibility).
    Returns flights sorted by price.
    """
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[FLIGHT_AGENT] {message}")
    
    def search(self, origin: str, destination: str, depart_date: str, return_date: str | None=None, passengers:int=1, budget: float | None=None) -> List[Dict[str,Any]]:
        self._log(f"Searching flights: {origin} -> {destination}, {depart_date} to {return_date}, Budget: ${budget}")
        flights = amadeus_flights_search(origin, destination, depart_date, return_date, passengers)
        if not flights:
            self._log("No flights found")
            return []
        self._log(f"Found {len(flights)} flights")
        flights_sorted = sorted(flights, key=lambda f: f.get("price", float('inf')))
        if budget:
            affordable = [f for f in flights_sorted if f.get("price", float('inf')) <= budget]
            self._log(f"Filtered to {len(affordable)} affordable flights (budget: ${budget})")
            return affordable if affordable else flights_sorted
        return flights_sorted

# Test client
# def main():
#     agent = FlightAgent()
#     flights = agent.search(
#         origin="SIN",
#         destination="BKK",
#         depart_date="2026-03-01",
#         return_date=None,
#         passengers=1,
#         budget=500.0,
#     )
#     print(f"Found {len(flights)} flights")
#     for f in flights[:5]:
#         print(f)


# if __name__ == "__main__":
#     main()