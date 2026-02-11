from langchain_openai import ChatOpenAI
from tools.restaurant_tool import search_restaurants # restaurant tool with mock data

llm = ChatOpenAI(model="gpt-4o-mini")

# ACCESS CONTROL: This agent can ONLY see and call search_restaurants
restaurant_llm = llm.bind_tools([search_restaurants])

def restaurant_agent(state: MultiAgentState):
    prompt = "You are a food critic. You have access to restaurant search tools only. Find restaurants that match the user's budget and taste."
    response = restaurant_llm.invoke([("system", prompt)] + state["messages"])
    return {"messages": [response]}