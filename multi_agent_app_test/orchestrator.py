from langgraph.graph import StateGraph, START, END
from state import MultiAgentState
from supervisor import supervisor_node
from agents.flight_agent import flight_agent
from agents.hotel_agent import hotel_agent
from agents.restaurant_agent import restaurant_agent
from agents.budget_agent import budget_agent
from langgraph.prebuilt import ToolNode
from tools.flight_tool import search_flights
from tools.restaurant_tool import search_restaurants
from tools.hotel_tool import search_hotels

# This node acts as the shared 'execution engine'
all_tools = [search_flights, search_restaurants, search_hotels]
tool_node = ToolNode(all_tools)

def create_travel_graph():
    # 1. Initialize the StateGraph
    workflow = StateGraph(MultiAgentState)

    # 2. Add the Supervisor and the Worker Agents and Tools
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("flight_agent", flight_agent)
    workflow.add_node("hotel_agent", hotel_agent)
    workflow.add_node("restaurant_agent", restaurant_agent)
    workflow.add_node("budget_agent", budget_agent)
    workflow.add_node("tools", tool_node)

    # 3. The Logic: Always start with the Supervisor
    workflow.add_edge(START, "supervisor")

    # 4. The Routing: Based on supervisor's decision in 'next_agent'
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next_agent"], # This reads the output from supervisor_node
        {
            "flight_agent": "flight_agent",
            "hotel_agent": "hotel_agent",
            "restaurant_agent": "restaurant_agent",
            "budget_agent": "budget_agent",
            "FINISH": END
        }
    )

    # 5. The Handoff: Every agent must report back to the supervisor when done
    workflow.add_edge("flight_agent", "supervisor")
    workflow.add_edge("hotel_agent", "supervisor")
    workflow.add_edge("restaurant_agent", "supervisor")
    workflow.add_edge("budget_agent", "supervisor")

    return workflow.compile()

# Generate the app instance
app = create_travel_graph()