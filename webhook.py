"""
webhook.py — Paystack webhook listener.

Run this SEPARATELY from the Streamlit app using:
    python webhook.py

This listens on port 4242 for Paystack events (payment success, cancellation)
and automatically updates user plan status in users.json.

Setup:
1. Install Flask: pip install flask
2. Run: python webhook.py
3. In Paystack Dashboard → Settings → API Keys & Webhooks:
   Webhook URL: http://your-server-ip:4242/webhook
   Paystack will send events to this URL automatically.

Events handled:
    charge.success          → activates user subscription
    subscription.disable    → cancels user subscription
    invoice.payment_failed  → flags subscription as inactive
"""

import json
import os
from flask import Flask, request, jsonify
from billing.paystack_handler import verify_webhook, handle_webhook_event
from auth.user_db import activate_subscription, cancel_subscription, update_user

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def paystack_webhook():
    payload   = request.data
    signature = request.headers.get("x-paystack-signature", "")

    # ── Verify the request is genuinely from Paystack ─────────
    if not verify_webhook(payload, signature):
        print("❌ Invalid webhook signature — rejected.")
        return jsonify({"error": "Invalid signature"}), 400

    event = json.loads(payload.decode("utf-8"))
    event_type, data = handle_webhook_event(event)
    print(f"📩 Paystack event received: {event_type}")

    # ── Payment succeeded → activate subscription ──────────────
    if event_type == "charge.success":
        metadata   = data.get("metadata", {})
        user_email = metadata.get("user_email")
        plan       = metadata.get("plan")
        customer   = data.get("customer", {})
        customer_code = customer.get("customer_code")
        subscription_code = data.get("subscription_code", "")

        if user_email and plan:
            activate_subscription(
                email=user_email,
                plan=plan,
                paystack_customer_code=customer_code,
                paystack_subscription_code=subscription_code
            )
            print(f"✅ '{plan}' plan activated for {user_email}")

    # ── New subscription created ───────────────────────────────
    elif event_type == "subscription.create":
        customer      = data.get("customer", {})
        user_email    = customer.get("email")
        plan_data     = data.get("plan", {})
        plan_name     = plan_data.get("name", "").lower()
        sub_code      = data.get("subscription_code")
        customer_code = customer.get("customer_code")

        # Map Paystack plan name to our internal plan key
        plan = "pro" if "pro" in plan_name else "basic"

        if user_email:
            activate_subscription(
                email=user_email,
                plan=plan,
                paystack_customer_code=customer_code,
                paystack_subscription_code=sub_code
            )
            print(f"✅ Subscription created: '{plan}' for {user_email}")

    # ── Subscription cancelled ─────────────────────────────────
    elif event_type == "subscription.disable":
        customer   = data.get("customer", {})
        user_email = customer.get("email")

        if user_email:
            cancel_subscription(user_email)
            print(f"❌ Subscription cancelled for {user_email}")

    # ── Recurring payment failed ───────────────────────────────
    elif event_type == "invoice.payment_failed":
        customer   = data.get("customer", {})
        user_email = customer.get("email")

        if user_email:
            update_user(user_email, {"subscription_active": False})
            print(f"⚠️  Payment failed for {user_email} — plan suspended.")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
# 1. Use Render's dynamic port if available, otherwise default to 4242 locally
    port = int(os.environ.get("PORT", 4242))
    
    print(f"🎧 Paystack webhook listener running on port {port}...")
    print(f"📌 Point your Paystack webhook to your Render URL")
    
    # 2. CRITICAL: Added host="0.0.0.0" so Render can route traffic to it
    app.run(host="0.0.0.0", port=port, debug=False)
