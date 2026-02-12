from typing import List, Dict, Any
from tools.scraper import amadeus_flights_search

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

# Test client
def main():
    agent = FlightAgent()
    flights = agent.search(
        origin="SIN",
        destination="BKK",
        depart_date="2026-03-01",
        return_date=None,
        passengers=1,
        budget=500.0,
    )
    print(f"Found {len(flights)} flights")
    for f in flights[:5]:
        print(f)


if __name__ == "__main__":
    main()