"""
pages/pricing.py — Pricing plans and Stripe checkout.
"""

import streamlit as st
from auth.user_db import get_plan, get_user, trial_days_remaining, PLAN_LIMITS


def show():
    email   = st.session_state.user_email
    plan    = get_plan(email)
    user    = get_user(email)

    st.title("💳 Plans & Pricing")
    st.caption("Choose the plan that fits your business. Cancel anytime.")
    st.divider()

    # ─── Trial status banner ──────────────────────────────────────
    if plan == "trial":
        days = trial_days_remaining(email)
        st.info(f"⏳ You're on the **Free Trial** with **{days} days remaining**.")
    elif plan == "expired":
        st.error("❌ Your trial or subscription has expired. Subscribe below to continue.")
    elif plan == "basic":
        st.success("✅ You're on the **Basic Plan**.")
    elif plan == "pro":
        st.success("✅ You're on the **Pro Plan**.")

    st.divider()

    # ─── Pricing cards ────────────────────────────────────────────
    col_basic, col_pro = st.columns(2)

    # Basic Plan
    with col_basic:
        st.markdown("### 🥈 Basic")
        st.markdown("## $9 / month")
        st.caption("Perfect for freelancers and small businesses")
        st.divider()

        features_basic = [
            "✅ Up to 100 clients",
            "✅ 3 follow-up attempts",
            "✅ 50 emails per day",
            "✅ Custom follow-up schedule",
            "✅ Activity logs",
            "✅ Gmail integration",
            "✅ AI-written emails (Groq)",
            "❌ Priority support",
        ]
        for f in features_basic:
            st.write(f)

        st.divider()

        if plan == "basic":
            st.success("✅ Current Plan")
            if user.get("stripe_customer_id"):
                if st.button("Manage Subscription", use_container_width=True, key="manage_basic"):
                    try:
                        from billing.stripe_handler import create_billing_portal_session
                        url = create_billing_portal_session(user["stripe_customer_id"])
                        st.markdown(f"[Open Billing Portal]({url})")
                    except Exception as e:
                        st.error(f"Could not open billing portal: {e}")
        elif plan == "pro":
            st.info("You're on a higher plan.")
        else:
            if st.button("🚀 Subscribe — Basic", type="primary", use_container_width=True):
                try:
                    from billing.stripe_handler import create_checkout_session
                    url = create_checkout_session(email, "basic")
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="0; url={url}">
                    <a href="{url}" target="_blank">Click here if not redirected automatically</a>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not create checkout session: {e}")
                    st.info("Make sure STRIPE_SECRET_KEY and STRIPE_PRICE_BASIC are set in your .env file.")

    # Pro Plan
    with col_pro:
        st.markdown("### 🥇 Pro")
        st.markdown("## $29 / month")
        st.caption("For agencies and growing teams")
        st.divider()

        features_pro = [
            "✅ Unlimited clients",
            "✅ 5 follow-up attempts",
            "✅ 200 emails per day",
            "✅ Custom follow-up schedule",
            "✅ Activity logs",
            "✅ Gmail integration",
            "✅ AI-written emails (Groq)",
            "✅ Priority support",
        ]
        for f in features_pro:
            st.write(f)

        st.divider()

        if plan == "pro":
            st.success("✅ Current Plan")
            if user.get("stripe_customer_id"):
                if st.button("Manage Subscription", use_container_width=True, key="manage_pro"):
                    try:
                        from billing.stripe_handler import create_billing_portal_session
                        url = create_billing_portal_session(user["stripe_customer_id"])
                        st.markdown(f"[Open Billing Portal]({url})")
                    except Exception as e:
                        st.error(f"Could not open billing portal: {e}")
        else:
            if st.button("🚀 Subscribe — Pro", type="primary", use_container_width=True):
                try:
                    from billing.stripe_handler import create_checkout_session
                    url = create_checkout_session(email, "pro")
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="0; url={url}">
                    <a href="{url}" target="_blank">Click here if not redirected automatically</a>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not create checkout session: {e}")
                    st.info("Make sure STRIPE_SECRET_KEY and STRIPE_PRICE_PRO are set in your .env file.")

    st.divider()

    # ─── FAQ ─────────────────────────────────────────────────────
    st.subheader("❓ Frequently Asked Questions")

    with st.expander("Can I cancel anytime?"):
        st.write("Yes. Cancel from the billing portal with one click. "
                 "You keep access until the end of your billing period.")

    with st.expander("What happens when my trial expires?"):
        st.write("Your bot pauses and you'll be prompted to subscribe. "
                 "No data is deleted — everything resumes the moment you upgrade.")

    with st.expander("Do I need a credit card for the trial?"):
        st.write("No. The 2-day free trial requires no payment details at all.")

    with st.expander("Can I upgrade from Basic to Pro later?"):
        st.write("Yes. Upgrade anytime from this page. "
                 "Stripe will prorate the difference automatically.")

    with st.expander("Is my Gmail password stored?"):
        st.write("Never. The app uses Google OAuth — only a secure token is stored locally. "
                 "You can revoke access from your Google account at any time.")
