from datetime import datetime
from typing import Dict

def nights_between(start_date: str, end_date: str) -> int:
    s = datetime.fromisoformat(start_date)
    e = datetime.fromisoformat(end_date)
    days = max((e - s).days, 0)
    return days

def allocate_budget(total_budget: float, custom_allocation: Dict[str, float] | None = None) -> Dict[str, float]:
    default_pct = {"flight": 0.30, "hotel": 0.40, "restaurant": 0.30}
    if custom_allocation:
        total_pct = sum(custom_allocation.values())
        if total_pct <= 0:
            alloc_pct = default_pct
        else:
            # normalize keys to flight/hotel/restaurant
            alloc_pct = {}
            for k in ["flight","hotel","restaurant"]:
                alloc_pct[k] = custom_allocation.get(k, default_pct[k]) / total_pct
    else:
        alloc_pct = default_pct
    allocation = {k: round(total_budget * v, 2) for k, v in alloc_pct.items()}
    # round mismatch
    diff = round(total_budget - sum(allocation.values()), 2)
    if diff != 0:
        allocation["restaurant"] = round(allocation.get("restaurant", 0) + diff, 2)
    return allocation

def close_to_budget(candidate_total: float, target_budget: float, tolerance: float = 0.05) -> bool:
    lower = target_budget * (1 - tolerance)
    upper = target_budget * (1 + tolerance)
    return lower <= candidate_total <= upper
