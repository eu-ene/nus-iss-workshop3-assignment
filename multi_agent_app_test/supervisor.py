from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from state import MultiAgentState

# Define the members (agents) the supervisor can manage
# members = ["flight_agent", "hotel_agent", "restaurant_agent", "budget_agent"]
# options = ["FINISH"] + members
# class RouteResponse(BaseModel):
#     """The decision of the supervisor on who should act next."""
#     next: Literal[*options]

# Define valid agents
VALID_AGENTS = ["flight_agent", "hotel_agent", "restaurant_agent", "budget_agent"]

class RouteResponse(BaseModel):
    """The decision of the supervisor on who should act next."""
    next_agent: Literal["flight_agent", "hotel_agent", "restaurant_agent", "budget_agent", "FINISH"]
    reasoning: str = Field(description="Short explanation of why this agent was chosen.")

    @field_validator("next_agent")
    def validate_agent(cls, v):
        if v not in VALID_AGENTS and v != "FINISH":
            raise ValueError(f"Supervisor tried to route to unknown agent: {v}")
        return v

llm = ChatOpenAI(model="gpt-4o-mini")

def supervisor_node(state: MultiAgentState):
    """
    Acts as the team lead. It reviews the conversation and picks 
    the best agent for the current task.
    """
    system_prompt = (
        "You are the Travel Manager. You must delegate tasks to specialists. "
        f"Available specialists: {VALID_AGENTS}. "
        "When all information is gathered and the budget is checked, respond with FINISH."
    )

# Structured Output Guardrail
    planner = llm.with_structured_output(RouteResponse)
    
    try:
        # Pass the history to the LLM
        response = planner.invoke([("system", system_prompt)] + state["messages"])
        
        # LOGIC GUARDRAIL: Prevent the supervisor from repeating a failed step
        # If the last 3 agents called were the same, force a 'FINISH' or 'budget_agent'
        last_three = [m.get("next_agent") for m in state["messages"][-3:] if isinstance(m, dict)]
        if len(last_three) == 3 and all(x == response.next_agent for x in last_three):
             return {"next_agent": "budget_agent", "messages": [("system", "Supervisor loop detected. Forcing budget check.")]}

        return {"next_agent": response.next_agent}

    except Exception as e:
        # FALLBACK GUARDRAIL: If the LLM fails to provide structured output
        print(f"Supervisor Guardrail Triggered: {e}")
        return {"next_agent": "FINISH", "messages": [("system", "Error in routing. Terminating session.")]}