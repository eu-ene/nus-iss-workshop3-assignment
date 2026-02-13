import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from travel_planner.orchestrator import TravelPlannerOrchestrator
import json

def print_separator(char="=", length=80):
    print(char * length)

def print_block(title, content=""):
    print_separator()
    print(f"  {title}")
    print_separator()
    if content:
        print(content)

def pretty_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)

def run_search(planner, config):
    """
    Run a travel search with given configuration.
    """
    print_block(f"SEARCH: {config['origin']} → {config['destination']}")
    print(f"Dates: {config['start_date']} to {config['end_date']}")
    print(f"Budget: ${config['budget']}")
    print(f"Cuisine: {config.get('cuisine', 'Any')}")
    print(f"Passengers: {config.get('passengers', 1)}")
    if config.get('allocation_override'):
        print(f"Custom Allocation: {config['allocation_override']}")
    print()
    
    plan = planner.plan(
        origin=config['origin'],
        destination=config['destination'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        budget=config['budget'],
        cuisine=config.get('cuisine'),
        passengers=config.get('passengers', 1),
        stars_preference=config.get('stars_preference'),
        allocation_override=config.get('allocation_override')
    )
    
    print_block("RESULTS", "")
    print(f"Total Cost: ${plan['costs']['subtotal']} / ${plan['costs']['budget']}")
    print(f"Flight: {plan['chosen_flight']['airline'] if plan['chosen_flight'] else 'None'} - ${plan['costs']['flight']}")
    print(f"Hotel: {plan['chosen_hotel']['name'] if plan['chosen_hotel'] else 'None'} - ${plan['costs']['hotel']}")
    print(f"Restaurants: {len(plan['chosen_restaurants'])} selected - ${plan['costs']['restaurant']}")
    print()
    
    print_block("SUMMARY")
    print(plan.get('summary'))
    print()
    
    return plan

def main():
    planner = TravelPlannerOrchestrator(verbose=True)
    
    # Define multiple search configurations
    searches = [
        {
            "origin": "singapore",
            "destination": "tokyo",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "budget": 1000.0,
            "cuisine": "ramen",
            "passengers": 1
        },
        {
            "origin": "SIN",
            "destination": "Bangkok",
            "start_date": "2026-07-10",
            "end_date": "2026-07-15",
            "budget": 400.0,
            "cuisine": "seafood",
            "passengers": 2
        },
        {
            "origin": "Singapore",
            "destination": "London",
            "start_date": "2026-06-01",
            "end_date": "2026-06-05",
            "budget": 2000.0,
            "cuisine": "indian",
            "allocation_override": {"flight": 0.25, "hotel": 0.60, "restaurant": 0.15}
        }
    ]
    
    # Run only the first search by default (change index to run different searches)
    selected_searches = [0]  # Change to [0, 1, 2] to run all searches
    
    for idx in selected_searches:
        if idx < len(searches):
            run_search(planner, searches[idx])
            print("\n" * 2)

if __name__ == "__main__":
    main()
