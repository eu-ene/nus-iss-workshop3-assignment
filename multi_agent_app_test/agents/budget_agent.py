import re
from langchain_openai import ChatOpenAI
from state import MultiAgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def budget_agent(state: MultiAgentState):
    """
    Calculates the total cost by parsing previous messages and 
    compares it against the user's limit.
    """
    messages = state["messages"]
    full_history = " ".join([str(m.content) for m in messages])
    
    # 1. Extract the initial budget from the user's first message
    # Looking for patterns like "$2000" or "2000 dollars"
    user_budget_match = re.search(r'\$?(\d{3,})', str(messages[0].content))
    limit = float(user_budget_match.group(1)) if user_budget_match else 0.0

    # 2. Extract all prices mentioned by tools/agents in the history
    # This regex finds numbers preceded by $
    all_prices = re.findall(r'\$(\d+(?:\.\d{2})?)', full_history)
    
    # We ignore the first price found if it matches the 'limit' 
    # (to avoid adding the budget limit to the total cost)
    current_total = sum(float(p) for p in all_prices) - limit
    remaining = limit - current_total

    # 3. Create a status report for the supervisor/user
    status = (
        f"BUDGET REPORT:\n"
        f"- Total Limit: ${limit:.2f}\n"
        f"- Current Spend: ${current_total:.2f}\n"
        f"- Remaining: ${remaining:.2f}\n"
    )
    
    if remaining < 0:
        status += "WARNING: You are over budget! Please find cheaper alternatives."
    else:
        status += "Budget is currently within limits."

    # 4. Use the LLM to format this into the conversation naturally
    response = llm.invoke(f"Summarize this budget status for the user: {status}")
    
    return {
        "messages": [response],
        "current_budget": current_total
    }