from typing import Dict, Any, Optional
from travel_planner.langgraph_adapter import LangGraphAdapter
from travel_planner.agents.flight_agent import FlightAgent
from travel_planner.agents.hotel_agent import HotelAgent
from travel_planner.agents.restaurant_agent import RestaurantAgent
from travel_planner.utils import nights_between, allocate_budget, close_to_budget
from travel_planner.llm.openai_client import rank_items_via_llm, summarize_plan_via_llm
from math import inf

class TravelPlannerOrchestrator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.graph = LangGraphAdapter()
        self.flight_agent = FlightAgent(verbose=verbose)
        self.hotel_agent = HotelAgent(verbose=verbose)
        self.restaurant_agent = RestaurantAgent(verbose=verbose)
        # Register nodes
        self.graph.add_node("flight_agent", self._flight_node)
        self.graph.add_node("hotel_agent", self._hotel_node)
        self.graph.add_node("restaurant_agent", self._restaurant_node)
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[ORCHESTRATOR] {message}")

    # Node wrappers
    def _flight_node(self, origin, destination, depart_date, return_date, passengers, flight_budget):
        return self.flight_agent.search(origin=origin, destination=destination, depart_date=depart_date, return_date=return_date, passengers=passengers, budget=flight_budget)

    def _hotel_node(self, destination, check_in, check_out, max_price_per_night, stars_preference):
        return self.hotel_agent.search(destination=destination, check_in=check_in, check_out=check_out, max_price_per_night=max_price_per_night, stars_preference=stars_preference)

    def _restaurant_node(self, destination, cuisine, limit):
        return self.restaurant_agent.search(destination=destination, cuisine=cuisine, limit=limit)

    def plan(self,
             origin: str,
             destination: str,
             start_date: str,
             end_date: str,
             budget: float,
             cuisine: Optional[str] = None,
             passengers: int = 1,
             stars_preference: Optional[int] = None,
             allocation_override: Optional[Dict[str, float]] = None,
             tolerance: float = 0.05) -> Dict[str, Any]:
        self._log(f"Starting travel planning: {origin} -> {destination}, {start_date} to {end_date}, Budget: ${budget}")
        
        nights = nights_between(start_date, end_date)
        if nights <= 0:
            raise ValueError("end_date must be after start_date")
        
        self._log(f"Trip duration: {nights} nights")
        allocation = allocate_budget(budget, allocation_override)
        self._log(f"Budget allocation: Flight=${allocation['flight']}, Hotel=${allocation['hotel']}, Restaurant=${allocation['restaurant']}")
        
        max_price_per_night = round(allocation["hotel"] / max(nights,1), 2)

        calls = {
            "flight_agent": {
                "origin": origin,
                "destination": destination,
                "depart_date": start_date,
                "return_date": end_date,
                "passengers": passengers,
                "flight_budget": allocation["flight"]
            },
            "hotel_agent": {
                "destination": destination,
                "check_in": start_date,
                "check_out": end_date,
                "max_price_per_night": max_price_per_night,
                "stars_preference": stars_preference
            },
            "restaurant_agent": {
                "destination": destination,
                "cuisine": cuisine,
                "limit": max(6, nights*2)
            }
        }

        self._log("Executing agents in parallel...")
        raw = self.graph.run_nodes_parallel(calls, max_workers=3)
        flights = raw.get("flight_agent", [])
        hotels = raw.get("hotel_agent", [])
        restaurants = raw.get("restaurant_agent", [])
        
        self._log(f"Agent results: {len(flights)} flights, {len(hotels)} hotels, {len(restaurants)} restaurants")

        # Pick candidate sets (top N)
        top_flights = flights[:3] if isinstance(flights, list) else []
        top_hotels = hotels[:3] if isinstance(hotels, list) else []
        top_restaurants = restaurants[:10] if isinstance(restaurants, list) else []

        # Ask LLM to rank each list (assists selection)
        self._log("Requesting LLM to rank candidates...")
        context = {"destination": destination, "start_date": start_date, "end_date": end_date, "cuisine": cuisine}
        
        self._log(f"  - Ranking {len(top_flights)} flights")
        ranked_flights = rank_items_via_llm("flight", top_flights, {**context, "role_budget": allocation["flight"]}, top_k=3, verbose=self.verbose) if top_flights else []
        
        self._log(f"  - Ranking {len(top_hotels)} hotels")
        ranked_hotels = rank_items_via_llm("hotel", top_hotels, {**context, "role_budget": allocation["hotel"]}, top_k=3, verbose=self.verbose) if top_hotels else []
        
        self._log(f"  - Ranking {len(top_restaurants)} restaurants")
        ranked_restaurants = rank_items_via_llm("restaurant", top_restaurants, {**context, "role_budget": allocation["restaurant"], "nights": nights}, top_k=6, verbose=self.verbose) if top_restaurants else []

        # Choose best candidates from LLM outputs (or fallback heuristics)
        chosen_flight = ranked_flights[0] if ranked_flights else (top_flights[0] if top_flights else None)
        chosen_hotel = ranked_hotels[0] if ranked_hotels else (top_hotels[0] if top_hotels else None)
        
        self._log(f"Selected: Flight={chosen_flight.get('airline') if chosen_flight else 'None'}, Hotel={chosen_hotel.get('name') if chosen_hotel else 'None'}")

        # Greedy restaurants pick until restaurant allocation exhausted
        chosen_restaurants = []
        remaining_rest_budget = allocation["restaurant"]
        for r in ranked_restaurants:
            price = r.get("estimated_price", 0) or r.get("avg_price", 0) or r.get("price", 0)
            if price == 0:
                chosen_restaurants.append(r)
                continue
            if price <= remaining_rest_budget:
                chosen_restaurants.append(r)
                remaining_rest_budget = round(remaining_rest_budget - price, 2)
        
        self._log(f"Selected {len(chosen_restaurants)} restaurants")

        # compute costs
        flight_cost = chosen_flight.get("price", 0) if chosen_flight else 0
        hotel_cost = (chosen_hotel.get("price_per_night", 0) * nights) if chosen_hotel else 0
        restaurants_cost = sum(r.get("estimated_price", 0) or r.get("avg_price", 0) for r in chosen_restaurants)
        subtotal = round(flight_cost + hotel_cost + restaurants_cost, 2)
        
        self._log(f"Initial costs: Flight=${flight_cost}, Hotel=${hotel_cost}, Restaurant=${restaurants_cost}, Subtotal=${subtotal}")

        # Progressive relaxation if subtotal > budget
        if subtotal > budget:
            self._log(f"Over budget by ${subtotal - budget}. Starting progressive relaxation...")
            # 1) prune restaurants (remove most expensive)
            chosen_restaurants.sort(key=lambda x: x.get("estimated_price",0), reverse=True)
            while chosen_restaurants and subtotal > budget:
                removed = chosen_restaurants.pop(0)
                subtotal = round(subtotal - removed.get("estimated_price",0),2)
                self._log(f"  - Removed restaurant: {removed.get('name')}, New subtotal=${subtotal}")

        if subtotal > budget:
            self._log("  - Searching for cheaper hotels (80% budget)...")
            # 2) ask hotel agent for cheaper hotels (reduce per-night to 80%)
            alt_hotels = self._hotel_node(destination=destination, check_in=start_date, check_out=end_date, max_price_per_night=round(max_price_per_night*0.8,2), stars_preference=stars_preference)
            if alt_hotels:
                alt_h = alt_hotels[0]
                alt_cost = alt_h.get("price_per_night",0) * nights
                if alt_cost < hotel_cost:
                    self._log(f"  - Found cheaper hotel: {alt_h.get('name')}, ${alt_cost} vs ${hotel_cost}")
                    chosen_hotel = alt_h
                    hotel_cost = alt_cost
                    subtotal = round(flight_cost + hotel_cost + restaurants_cost,2)

        if subtotal > budget:
            self._log("  - Searching for cheaper flights (90% budget)...")
            # 3) ask flight agent for cheaper flights below current flight allocation*0.9
            alt_flights = self._flight_node(origin=origin, destination=destination, depart_date=start_date, return_date=end_date, passengers=passengers, flight_budget=round(allocation["flight"]*0.9,2))
            if alt_flights:
                alt_f = alt_flights[0]
                if alt_f.get("price",inf) < flight_cost:
                    self._log(f"  - Found cheaper flight: {alt_f.get('airline')}, ${alt_f.get('price')} vs ${flight_cost}")
                    chosen_flight = alt_f
                    flight_cost = alt_f.get("price",0)
                    subtotal = round(flight_cost + hotel_cost + restaurants_cost,2)
        
        self._log(f"Final costs: Flight=${flight_cost}, Hotel=${hotel_cost}, Restaurant=${restaurants_cost}, Subtotal=${subtotal}")

        within_tolerance = close_to_budget(subtotal, budget, tolerance)
        plan = {
            "nights": nights,
            "allocation": allocation,
            "chosen_flight": chosen_flight,
            "chosen_hotel": chosen_hotel,
            "chosen_restaurants": chosen_restaurants,
            "costs": {
                "flight": round(flight_cost,2),
                "hotel": round(hotel_cost,2),
                "restaurant": round(restaurants_cost,2),
                "subtotal": round(subtotal,2),
                "budget": round(budget,2)
            },
            "within_tolerance": within_tolerance,
            "notes": "LLM used to assist ranking; orchestrator performed progressive relaxation."
        }

        # Ask LLM to generate final textual itinerary
        self._log("Requesting LLM to generate summary...")
        plan_summary = summarize_plan_via_llm(plan, verbose=self.verbose)
        plan["summary"] = plan_summary
        self._log("Planning complete!")
        return plan
