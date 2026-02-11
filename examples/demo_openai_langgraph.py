from travel_planner.orchestrator import TravelPlannerOrchestrator
import json

def pretty(plan):
    print(json.dumps(plan, indent=2, ensure_ascii=False))

def main():
    planner = TravelPlannerOrchestrator()
    origin = "SIN"
    destination = "Bangkok"
    start_date = "2026-06-01"
    end_date = "2026-06-05"
    budget = 1000.0
    cuisine = "seafood"

    print("=== DEFAULT allocation (30/40/30) ===")
    plan_default = planner.plan(origin=origin, destination=destination, start_date=start_date, end_date=end_date, budget=budget, cuisine=cuisine)
    pretty(plan_default)
    print("\n--- Human-friendly summary ---")
    print(plan_default.get("summary"))

    # Custom allocation example
    alloc_override = {"flight":0.25, "hotel":0.60, "restaurant":0.15}
    print("\n=== CUSTOM allocation (25/60/15) ===")
    plan_custom = planner.plan(origin=origin, destination=destination, start_date=start_date, end_date=end_date, budget=budget, cuisine=cuisine, allocation_override=alloc_override)
    pretty(plan_custom)
    print("\n--- Human-friendly summary ---")
    print(plan_custom.get("summary"))

if __name__ == "__main__":
    main()
