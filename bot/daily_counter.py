"""
daily_counter.py — Tracks how many emails have been sent today.
Resets automatically at midnight every day.
Persists to disk so the count survives bot restarts.
"""

import os
import json
from datetime import datetime

COUNTER_FILE = "daily_send_counter.json"


def _load() -> dict:
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return json.load(f)
    return {}


def _save(data: dict):
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)


def get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_sent_today() -> int:
    """Return how many emails have been sent so far today."""
    data = _load()
    today = get_today()
    if data.get("date") != today:
        return 0  # new day — counter hasn't been reset yet but reads as 0
    return data.get("count", 0)


def increment(amount: int = 1):
    """Record that `amount` emails were just sent."""
    data  = _load()
    today = get_today()

    if data.get("date") != today:
        # New day — reset counter
        data = {"date": today, "count": 0}

    data["count"] = data.get("count", 0) + amount
    _save(data)


def reset():
    """Manually reset the counter to zero for today."""
    _save({"date": get_today(), "count": 0})


def can_send(daily_limit) -> bool:
    """
    Return True if we haven't hit today's daily limit yet.
    Pass None for Enterprise (unlimited) — always returns True.
    """
    if daily_limit is None:
        return True   # Enterprise — no cap
    return get_sent_today() < daily_limit


def remaining(daily_limit) -> int:
    """
    Return how many more emails can be sent today.
    Returns None for Enterprise (unlimited).
    """
    if daily_limit is None:
        return None   # Enterprise — unlimited
    return max(0, daily_limit - get_sent_today())
