"""
billing/stripe_handler.py — Handles Stripe checkout sessions and webhooks.
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ─── Your Stripe Price IDs (create these in Stripe dashboard) ────
# Go to Stripe Dashboard > Products > Create Product > Add Price
# Copy the price ID (starts with price_) and paste below
PRICE_IDS = {
    "basic": os.getenv("STRIPE_PRICE_BASIC"),   # e.g. price_1ABC...
    "pro":   os.getenv("STRIPE_PRICE_PRO"),     # e.g. price_1XYZ...
}

APP_URL = os.getenv("APP_URL", "http://localhost:8501")


def create_checkout_session(user_email: str, plan: str) -> str | None:
    """
    Create a Stripe checkout session for the given plan.
    Returns the checkout URL to redirect the user to.
    """
    price_id = PRICE_IDS.get(plan)
    if not price_id:
        raise ValueError(f"No Stripe price ID configured for plan: {plan}")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{APP_URL}?page=dashboard&payment=success&plan={plan}",
        cancel_url=f"{APP_URL}?page=pricing&payment=cancelled",
        metadata={"user_email": user_email, "plan": plan},
    )

    return session.url


def create_billing_portal_session(stripe_customer_id: str) -> str:
    """
    Opens Stripe's hosted billing portal so users can manage/cancel their subscription.
    """
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{APP_URL}?page=dashboard",
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str) -> dict | None:
    """
    Verify and parse incoming Stripe webhook events.
    Call this from your webhook endpoint.
    Returns the event dict or None if verification fails.
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        return event
    except stripe.error.SignatureVerificationError:
        return None
