# Travel Planner - Multi-Agent System

An intelligent travel planning system that uses specialized agents to search for flights, hotels, and restaurants, coordinated through a LangGraph-inspired orchestrator with OpenAI LLM integration for ranking and itinerary generation.

## Features

- **Multi-Agent Architecture**: Specialized agents for flights (Amadeus API), hotels (SerpAPI/Google Hotels), and restaurants (Mock Data)
- **LLM-Powered Ranking**: OpenAI GPT integration for intelligent ranking and itinerary generation
- **Budget Optimization**: Automatic budget allocation with progressive relaxation strategy
- **Parallel Execution**: Concurrent agent execution using ThreadPoolExecutor
- **Flexible Configuration**: Customizable budget allocation and preferences
- **Verbose Logging**: Detailed interaction logs between orchestrator, agents, and LLM

## Architecture

### System Flow

```
User Request
     |
     v
Orchestrator (plan method)
     |
     |-- Budget Allocation (utils.py)
     |
     v
LangGraph Adapter (parallel execution)
     |
     |-- FlightAgent --> Amadeus API (scraper.py)
     |-- HotelAgent --> SerpAPI/Google Hotels (scraper.py)
     |-- RestaurantAgent --> Mock Data (scraper.py)
     |
     v
Raw Results (flights, hotels, restaurants)
     |
     v
LLM Ranking (openai_client.py)
     |
     v
Candidate Selection
     |
     v
Budget Validation
     |
     |-- Over Budget? --> Progressive Relaxation
     |                    (re-query agents with lower budgets)
     |
     v
Final Plan Assembly
     |
     v
LLM Summarization (openai_client.py)
     |
     v
Return Plan to User
```

### Components

**Orchestrator** (`orchestrator.py`)
- Entry point for travel planning
- Allocates budget across services (default: 30% flights, 40% hotels, 30% restaurants)
- Coordinates parallel agent execution via LangGraph Adapter
- Implements progressive relaxation when over budget (removes restaurants, searches cheaper hotels/flights)
- Generates final plan with LLM summary
- Supports custom budget allocation via `allocation_override` parameter

**Agents** (`agents/`)
- **FlightAgent**: Calls Amadeus API via scraper, filters by budget, sorts by price
- **HotelAgent**: Calls SerpAPI via scraper, filters by price/stars
- **RestaurantAgent**: Uses mock data via scraper, filters by cuisine
- All agents support verbose logging for debugging

**Tools** (`tools/scraper.py`)
- `amadeus_flights_search()`: Amadeus Flight Offers API integration with IATA code resolution and city-to-airport mapping
- `agoda_search()`: SerpAPI Google Hotels integration with fallback to mock data
- `mock_restaurants_search()`: Mock restaurant data with average prices for budget estimation

**LangGraph Adapter** (`langgraph_adapter.py`)
- Registers agent nodes
- Executes nodes in parallel using ThreadPoolExecutor
- Returns aggregated results

**LLM Client** (`llm/openai_client.py`)
- `rank_items_via_llm()`: Scores candidates 1-100 based on price, rating, convenience, and context
- `summarize_plan_via_llm()`: Generates human-friendly itinerary with budget breakdown
- Fallback to heuristic scoring if OpenAI unavailable

**Utilities** (`utils.py`)
- `allocate_budget()`: Splits total budget by percentage with automatic normalization
- `nights_between()`: Calculates trip duration from dates
- `close_to_budget()`: Validates budget tolerance (default 5%)

## Installation

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your API credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your actual API keys:

```env
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
SERPAPI_API_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

**Security Note:** Never commit the `.env` file to version control. It's already included in `.gitignore`.

## Usage

### Basic Example

```python
from travel_planner.orchestrator import TravelPlannerOrchestrator

planner = TravelPlannerOrchestrator(verbose=True)

plan = planner.plan(
    origin="singapore",
    destination="tokyo",
    start_date="2026-06-01",
    end_date="2026-06-05",
    budget=1000.0,
    cuisine="ramen",
    passengers=1
)

print(plan["summary"])
```

### Custom Budget Allocation

```python
# Allocate 25% flight, 60% hotel, 15% restaurant
custom_allocation = {"flight": 0.25, "hotel": 0.60, "restaurant": 0.15}

plan = planner.plan(
    origin="Singapore",
    destination="London",
    start_date="2026-06-01",
    end_date="2026-06-05",
    budget=2000.0,
    cuisine="indian",
    allocation_override=custom_allocation
)
```

### Run Demo

```bash
cd nus-iss-workshop3-assignment
python demo.py
```

The demo includes multiple pre-configured searches. Edit `selected_searches` in `demo.py` to run different scenarios:
- `[0]` - Tokyo trip with ramen cuisine
- `[1]` - Bangkok trip with seafood
- `[2]` - London trip with custom allocation
- `[0, 1, 2]` - Run all searches

## Project Structure

```
nus-iss-workshop3-assignment/
├── travel_planner/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── flight_agent.py      # Amadeus flight search
│   │   ├── hotel_agent.py       # SerpAPI hotel search
│   │   └── restaurant_agent.py  # Mock restaurant search
│   ├── llm/
│   │   ├── __init__.py
│   │   └── openai_client.py     # LLM ranking & summarization
│   ├── tools/
│   │   ├── __init__.py
│   │   └── scraper.py           # API integrations
│   ├── __init__.py
│   ├── config.py                # Settings & environment
│   ├── langgraph_adapter.py     # Parallel execution coordinator
│   ├── orchestrator.py          # Main orchestration logic
│   └── utils.py                 # Helper functions
├── .env.example                 # Environment template
├── .gitignore
├── demo.py                      # Demo script with examples
├── README.md
└── requirements.txt
```

### Verbose Logging
When `verbose=True`, the system logs:
- `[ORCHESTRATOR]` - Planning steps and decisions
- `[FLIGHT_AGENT]` - Flight search and filtering
- `[HOTEL_AGENT]` - Hotel search and filtering
- `[RESTAURANT_AGENT]` - Restaurant search
- `[AGODA_SEARCH]` - SerpAPI calls and results
- `[LLM]` - Ranking and summarization requests

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `python-dotenv` - Environment management
- `pydantic` - Settings validation
- `pydantic-settings` - Settings from environment
- `rich` - Terminal formatting
- `amadeus` - Flight API SDK
- `openai` - LLM integration (v1.0+)
- `langgraph` - Optional graph coordination

## API Integrations

### Amadeus (Flights)
- Flight search with IATA code resolution
- Automatic city-to-airport code mapping
- Fallback to mock data if API unavailable

### SerpAPI (Hotels)
- Google Hotels search via SerpAPI
- Real-time pricing and availability
- Fallback to mock data if API unavailable or no key configured

### Mock Data (Restaurants)
- Pre-configured restaurants for major cities (Tokyo, Bangkok, London, San Francisco)
- Includes average prices for budget estimation
- Cuisine and price level filtering

## Notes

- Mock data provided for restaurants and when APIs are unavailable
- Supports Zscaler SSL certification via `truststore`
- All prices in USD by default
- Minimum 1 night stay required
- API keys are masked in verbose output for security

## Troubleshooting

### API Key Issues
- Ensure `.env` file is in the project root
- Check API key length (Amadeus: varies, SerpAPI: 64 chars, OpenAI: starts with `sk-`)
- Verify no duplicate keys in `.env`

### No Hotels Found
- Check SerpAPI key is valid
- Verify budget allocation allows sufficient hotel budget
- System will fall back to mock data if API fails

### LLM Errors
- Ensure OpenAI API key is valid
- Check model name (default: `gpt-4o-mini`)
- System will fall back to heuristic ranking if LLM unavailable

