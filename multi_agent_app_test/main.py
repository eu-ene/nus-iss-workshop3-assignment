from graph import app

def chat_with_agent(user_prompt: str):
    config = {"configurable": {"thread_id": "user_session_1", "recursion_limit": 25}}
    initial_state = {
        "messages": [("user", user_prompt)],
        "current_budget": 0.0,
        "next_agent": ""
    }
    
    # Run the graph and stream the output
    for output in app.stream(initial_state, config):
        # This shows you which agent is currently working
        print(output)

if __name__ == "__main__":
    chat_with_agent("I need a flight and hotel for Tokyo under $2500.")