import os
import json
from typing import List, Dict, Any, Optional
import openai
from travel_planner.config import settings

openai_api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

MODEL = settings.OPENAI_MODEL or "gpt-4o-mini"

def rank_items_via_llm(role: str, candidates: List[Dict[str, Any]], context: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Ask OpenAI to rank candidate items for a role (flight/hotel/restaurant).
    Returns top_k candidates with a 'score' field (1..100).
    If OpenAI not configured, returns the input candidates with heuristic scoring.
    """
    if not openai_api_key:
        # heuristic: rank by price ascending (lower better) and rating / estimated_price
        scored = []
        for c in candidates:
            price = float(c.get("price", c.get("price_per_night", c.get("estimated_price", 0)) or 0) or 0)
            rating = float(c.get("rating", 0) or 0)
            # simple score: normalized
            score = max(1, 100 - price + rating)
            c_copy = dict(c)
            c_copy["score"] = round(score,2)
            scored.append(c_copy)
        scored_sorted = sorted(scored, key=lambda x: -x["score"])
        return scored_sorted[:top_k]

    # Prepare a compact prompt
    prompt = f"""
You are an assistant that ranks {role} options for a traveler.

Context:
- destination: {context.get('destination')}
- dates: {context.get('start_date')} to {context.get('end_date')}
- budget allocation for {role}: {context.get('role_budget')}

Candidates (JSON list). For each candidate, return a numeric score 1-100 (higher is better),
considering price, convenience, stops (for flights), rating (for hotels), estimated price (restaurants),
and the user's cuisine preference: {context.get('cuisine')}.

Return a JSON array of the top {top_k} candidates, each containing the original candidate fields plus a numeric "score".
Candidates:
{json.dumps(candidates[:20], indent=2)}
Provide only the JSON array as output.
"""
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role":"system","content":"You rank travel options."},
                      {"role":"user","content":prompt}],
            temperature=0.0,
            max_tokens=400
        )
        text = resp["choices"][0]["message"]["content"]
        # try to extract JSON
        text = text.strip()
        # If the model returns text with backticks, remove them
        if text.startswith("```"):
            # strip code fences
            text = "\n".join(line for line in text.splitlines() if not line.startswith("```"))
        parsed = json.loads(text)
        # ensure list
        if isinstance(parsed, list):
            return parsed[:top_k]
        # otherwise fallback
        return []
    except Exception as e:
        # fallback heuristic
        scored = []
        for c in candidates:
            price = float(c.get("price", c.get("price_per_night", c.get("estimated_price", 0)) or 0) or 0)
            rating = float(c.get("rating", 0) or 0)
            score = max(1, 100 - price + rating)
            c_copy = dict(c)
            c_copy["score"] = round(score,2)
            scored.append(c_copy)
        scored_sorted = sorted(scored, key=lambda x: -x["score"])
        return scored_sorted[:top_k]

def summarize_plan_via_llm(plan: Dict[str, Any]) -> str:
    """
    Ask OpenAI to create a human-friendly itinerary summary.
    """
    if not openai_api_key:
        # simple local summary
        s = []
        s.append(f"Trip for {plan.get('nights')} nights. Budget: {plan['costs'].get('budget')}.")
        s.append(f"Flight: {plan['chosen_flight']}")
        s.append(f"Hotel: {plan['chosen_hotel']}")
        s.append(f"Restaurants: {plan['chosen_restaurants']}")
        s.append(f"Costs: {plan['costs']}")
        return "\n".join(s)

    prompt = f"""
Given the following travel plan (JSON), produce a concise, user-friendly itinerary:
{json.dumps(plan, indent=2)}
Return only the final textual itinerary (no JSON).
"""
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role":"system","content":"You are a helpful travel assistant."},
                      {"role":"user","content":prompt}],
            temperature=0.2,
            max_tokens=400
        )
        text = resp["choices"][0]["message"]["content"].strip()
        return text
    except Exception:
        # fallback to local summary
        s = []
        s.append(f"Trip for {plan.get('nights')} nights. Budget: {plan['costs'].get('budget')}.")
        s.append(f"Flight: {plan['chosen_flight']}")
        s.append(f"Hotel: {plan['chosen_hotel']}")
        s.append(f"Restaurants: {plan['chosen_restaurants']}")
        s.append(f"Costs: {plan['costs']}")
        return "\n".join(s)
