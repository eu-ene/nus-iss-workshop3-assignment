# Travel Planner — LangGraph + OpenAI Multi-Agent Project

This project implements a **multi-agent Travel Planner** using a LangGraph-style adapter plus an OpenAI LLM to assist ranking and summarization.

Key components:
- **Orchestrator** — coordinates agents, allocates budget, negotiates alternatives.
- **FlightAgent** — obtains flight offers **only** from Amadeus Flight Offers API.
- **HotelAgent** — obtains hotels **only** from Agoda (placeholder/mock provided).
- **RestaurantAgent** — obtains restaurants **only** from TripAdvisor (HTTP parse + mock fallback).
- **LLM (OpenAI)** — used to score/rank candidates and produce user-facing summaries.

## Features
- Default budget allocation: **Flight 30% / Hotel 40% / Restaurant 30%**.
- User may override allocation: e.g., `{ "flight": 0.25, "hotel": 0.60, "restaurant": 0.15 }`.
- Agents are called **in parallel** using a LangGraph adapter.
- Orchestrator performs **progressive relaxation** if plan exceeds budget:
  - prune restaurants → request cheaper hotels → request cheaper flights.
- All external-scrape / API calls are centralized in `tools/scraper.py` to enforce the “only use” constraints.
- OpenAI is used only for ranking and summarization; heuristic fallback provided so the system still works offline.

## Folder Structure (Ideal state)
```
travel_planner_multi_agent/
├── main.py              # Entry point to run the system
├── state.py             # Shared state & TypedDict definitions
├── orchestrator.py      # Define edges and nodes, or known as `graph.py`
├── supervisor.py        # Manager logic (delegation & routing)
├── agents/
│   ├── flight_agent.py  # Flight specialist logic
│   ├── hotel_agent.py   # Hotel specialist logic
│   ├── restaurant_agent.py # Restaurant specialist logic
│   └── budget_agent.py  # Python-logic based budget checker
└── tools/
    ├── flight_tools.py
    ├── hotel_tools.py
    └── restaurant_tools.py
```

## Requirements & setup

1. Create and activate a venv:
   - Windows:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate
     ```
   - macOS / Linux:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
