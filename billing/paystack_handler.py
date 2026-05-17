"""
billing/paystack_handler.py — Handles Paystack payment integration.

Paystack is the leading payment gateway in Nigeria and Africa.
Supports cards, bank transfer, USSD, and mobile money.

Setup:
1. Sign up at https://paystack.com
2. Go to Settings → API Keys & Webhooks
3. Copy your Secret Key and Public Key into .env
4. Set up your webhook URL in the Paystack dashboard
"""

import os
import hmac
import hashlib
import json
import urllib.request
# FIXED: Removed unused 'import urllib.parse' to clear the linter warning
from dotenv import load_dotenv

load_dotenv()

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
APP_URL             = os.getenv("APP_URL", "http://localhost:8501")

PAYSTACK_BASE_URL   = "https://api.paystack.co"

# ─── Plan amounts in kobo (Paystack uses smallest currency unit) ──
# NGN: multiply naira by 100 to get kobo
# USD: multiply dollars by 100 to get cents
# Change these to match your pricing in your local currency
PLAN_AMOUNTS = {
    "basic": int(os.getenv("PLAN_BASIC_AMOUNT", 1500000)),   # e.g. ₦15,000/mo
    "pro":   int(os.getenv("PLAN_PRO_AMOUNT",   4500000)),   # e.g. ₦45,000/mo
}

# Paystack Plan Codes — create these in your Paystack dashboard
# Dashboard → Subscriptions → Plans → Create Plan → copy the plan_code
PLAN_CODES = {
    "basic": os.getenv("PAYSTACK_PLAN_CODE_BASIC"),   # e.g. PLN_xxxxxxxxxxxx
    "pro":   os.getenv("PAYSTACK_PLAN_CODE_PRO"),     # e.g. PLN_xxxxxxxxxxxx
}


def _paystack_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make an authenticated request to the Paystack API."""
    url     = f"{PAYSTACK_BASE_URL}{endpoint}"
    
    # FIXED: Added 'User-Agent' to circumvent Cloudflare 1010 Bot Checks
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type":  "application/json",
        "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req  = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"Paystack API error {e.code}: {error_body}")


def initialize_transaction(user_email: str, plan: str) -> str:
    """
    Initialize a Paystack transaction for a subscription plan.
    Returns the authorization URL to redirect the user to.

    Paystack handles the payment page — card details never touch your server.
    """
    plan_code = PLAN_CODES.get(plan)
    if not plan_code:
        raise ValueError(
            f"No Paystack plan code configured for '{plan}'. "
            f"Set PAYSTACK_PLAN_CODE_{plan.upper()} in your .env file."
        )

    payload = {
        "email":        user_email,
        "amount":       PLAN_AMOUNTS[plan],
        "plan":         plan_code,
        "callback_url": f"{APP_URL}?payment=success&plan={plan}&email={user_email}",
        "metadata": {
            "user_email": user_email,
            "plan":       plan,
            "cancel_action": f"{APP_URL}?payment=cancelled"
        }
    }

    response = _paystack_request("POST", "/transaction/initialize", payload)

    if not response.get("status"):
        raise Exception(f"Paystack initialization failed: {response.get('message')}")

    return response["data"]["authorization_url"]


def verify_transaction(reference: str) -> dict:
    """
    Verify a completed Paystack transaction by reference.
    Call this after the user returns from the Paystack payment page.
    Returns the transaction data including status and customer info.
    """
    response = _paystack_request("GET", f"/transaction/verify/{reference}")

    if not response.get("status"):
        raise Exception(f"Verification failed: {response.get('message')}")

    return response["data"]


def get_subscription(subscription_code: str) -> dict:
    """Fetch details of an existing subscription."""
    response = _paystack_request("GET", f"/subscription/{subscription_code}")
    return response.get("data", {})


def cancel_subscription(subscription_code: str, email_token: str) -> bool:
    """
    Cancel a Paystack subscription.
    subscription_code and email_token come from the subscription object.
    """
    payload  = {"code": subscription_code, "token": email_token}
    response = _paystack_request("POST", "/subscription/disable", payload)
    return response.get("status", False)


def verify_webhook(payload: bytes, paystack_signature: str) -> bool:
    """
    Verify that a webhook request genuinely came from Paystack.
    Uses HMAC SHA-512 signature verification.
    """
    if not PAYSTACK_SECRET_KEY:
        return False
        
    computed = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(computed, paystack_signature)


def handle_webhook_event(event: dict) -> tuple[str, dict]:
    """
    Parse a verified Paystack webhook event.
    Returns (event_type, data) tuple.

    Key event types:
        charge.success          — payment succeeded
        subscription.create     — new subscription started
        subscription.disable    — subscription cancelled
        invoice.payment_failed  — recurring payment failed
    """
    event_type = event.get("event", "")
    data       = event.get("data", {})
    return event_type, data