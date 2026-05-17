"""
auth/user_db.py — Manages user accounts, free trials, and plan status.
Stores everything in a local users.json file.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta

USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")

# ─── Plan feature limits ──────────────────────────────────────────
PLAN_LIMITS = {
    "trial": {
        "label": "Free Trial",
        "max_clients": 50,
        "max_followups": 1,
        "daily_send_limit": 50,
        "custom_schedule": False,
        "duration_days": 2,
    },
    "basic": {
        "label": "Basic",
        "price_monthly": 9,
        "max_clients": 200,
        "max_followups": 3,
        "daily_send_limit": 200,
        "custom_schedule": True,
    },
    "pro": {
        "label": "Pro",
        "price_monthly": 29,
        "max_clients": None,       # unlimited
        "max_followups": 5,
        "daily_send_limit": 500,
        "custom_schedule": True,
    },
    "enterprise": {
        "label": "Enterprise",
        "price_monthly": None,     # negotiated directly — no fixed price
        "max_clients": None,       # unlimited
        "max_followups": 10,
        "daily_send_limit": None,  # truly unlimited — no cap
        "custom_schedule": True,
    },
}


def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(email: str, password: str) -> tuple[bool, str]:
    """
    Create a new user account with a 2-day free trial.
    Returns (success, message).
    """
    users = _load_users()
    email = email.strip().lower()

    if email in users:
        return False, "An account with this email already exists."

    users[email] = {
        "password": _hash_password(password),
        "plan": "trial",
        "trial_started": datetime.now().isoformat(),
        "trial_expires": (datetime.now() + timedelta(days=2)).isoformat(),
        "paystack_customer_code":     None,
        "paystack_subscription_code": None,
        "subscription_active": False,
        "created_at": datetime.now().isoformat(),
        "settings": {
            "followup_schedule_days": [3, 7, 14],
            "max_followups": 1,
            "daily_send_limit": 10,
            "check_interval_mins": 30,
        },
        "bot_running": False,
    }

    _save_users(users)
    return True, "Account created! Your 2-day free trial has started."


def login_user(email: str, password: str) -> tuple[bool, str]:
    """Verify credentials. Returns (success, message)."""
    users = _load_users()
    email = email.strip().lower()

    if email not in users:
        return False, "No account found with this email."

    if users[email]["password"] != _hash_password(password):
        return False, "Incorrect password."

    return True, "Login successful."


def get_user(email: str) -> dict | None:
    """Return user record or None if not found."""
    users = _load_users()
    return users.get(email.strip().lower())


def update_user(email: str, updates: dict):
    """Merge updates into a user's record and save."""
    users = _load_users()
    email = email.strip().lower()
    if email in users:
        users[email].update(updates)
        _save_users(users)


def get_plan(email: str) -> str:
    """Return the user's current active plan ('trial', 'basic', 'pro', or 'expired')."""
    user = get_user(email)
    if not user:
        return "expired"

    plan = user.get("plan", "trial")

    if plan == "trial":
        expires = datetime.fromisoformat(user["trial_expires"])
        if datetime.now() > expires:
            return "expired"
        return "trial"

    if plan in ("basic", "pro", "enterprise"):
        if user.get("subscription_active"):
            return plan
        return "expired"

    return "expired"


def get_plan_limits(email: str) -> dict:
    """Return the feature limits for the user's current plan."""
    plan = get_plan(email)
    if plan == "expired":
        return {}
    return PLAN_LIMITS.get(plan, {})


def trial_days_remaining(email: str) -> float:
    """Return how many days remain on the free trial (0 if expired)."""
    user = get_user(email)
    if not user or user.get("plan") != "trial":
        return 0
    expires = datetime.fromisoformat(user["trial_expires"])
    remaining = (expires - datetime.now()).total_seconds() / 86400
    return max(0, round(remaining, 1))


def activate_subscription(email: str, plan: str, paystack_customer_code: str, paystack_subscription_code: str):
    """Called by Paystack webhook when payment succeeds."""
    update_user(email, {
        "plan": plan,
        "subscription_active": True,
        "paystack_customer_code":     paystack_customer_code,
        "paystack_subscription_code": paystack_subscription_code,
    })


def cancel_subscription(email: str):
    """Called by Stripe webhook when subscription is cancelled."""
    update_user(email, {
        "subscription_active": False,
    })


def save_settings(email: str, settings: dict):
    """Save the user's bot configuration settings."""
    users = _load_users()
    email = email.strip().lower()
    if email in users:
        users[email]["settings"].update(settings)
        _save_users(users)


def set_bot_running(email: str, running: bool):
    """Track whether the user's bot is currently active."""
    update_user(email, {"bot_running": running})


def assign_enterprise(email: str):
    """
    Manually assign Enterprise plan to a user.
    Call this yourself after negotiating with a company client.

    Usage — run this in a Python shell:
        from auth.user_db import assign_enterprise
        assign_enterprise("companyclient@example.com")
    """
    user = get_user(email)
    if not user:
        print(f"❌ No user found with email: {email}")
        return
    update_user(email, {
        "plan": "enterprise",
        "subscription_active": True,
        "paystack_customer_code": "manual",
        "paystack_subscription_code": "manual",
    })
    print(f"✅ Enterprise plan assigned to {email}")
