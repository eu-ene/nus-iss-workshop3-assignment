from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

class MultiAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str # Tracks who the supervisor picks next (e.g., "flight", "budget")
    current_budget: float
    # Optional: track the specific limit extracted by the budget agent
    budget_limit: float