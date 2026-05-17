"""
pages/pricing.py — Pricing plans and Paystack checkout.
"""

import streamlit as st
from auth.user_db import get_plan, get_user, trial_days_remaining, PLAN_LIMITS


def show():
    email = st.session_state.user_email
    plan  = get_plan(email)
    user  = get_user(email)

    st.title("💳 Plans & Pricing")
    st.caption("Choose the plan that fits your business. Cancel anytime.")
    st.divider()

    # ─── Trial/plan status banner ─────────────────────────────────
    if plan == "trial":
        days = trial_days_remaining(email)
        st.info(f"⏳ You're on the **Free Trial** with **{days} days remaining**.")
    elif plan == "expired":
        st.error("❌ Your trial or subscription has expired. Subscribe below to continue.")
    elif plan == "basic":
        st.success("✅ You're on the **Basic Plan**.")
    elif plan == "pro":
        st.success("✅ You're on the **Pro Plan**.")
    elif plan == "enterprise":
        st.success("✅ You're on the **Enterprise Plan**.")

    st.divider()

    # ─── Pricing cards: Basic + Pro ───────────────────────────────
    col_basic, col_pro = st.columns(2)

    # ── Basic ──────────────────────────────────────────────────────
    with col_basic:
        st.markdown("### 🥈 Basic")
        st.markdown("## $9 / month")
        st.caption("Perfect for freelancers and small businesses")
        st.divider()

        for f in [
            "✅ Up to 200 clients",
            "✅ 3 follow-up attempts",
            "✅ 200 emails per day",
            "✅ Custom follow-up schedule",
            "✅ Activity logs",
            "✅ Gmail integration",
            "✅ AI-written emails (Groq)",
            "❌ Priority support",
        ]:
            st.write(f)

        st.divider()

        if plan == "basic":
            st.success("✅ Current Plan")
            if user.get("paystack_subscription_code"):
                if st.button("Manage Subscription", use_container_width=True, key="manage_basic"):
                    st.info("To cancel or manage your subscription, contact us directly.")
        elif plan in ("pro", "enterprise"):
            st.info("You're on a higher plan.")
        else:
            if st.button("🚀 Subscribe — Basic", type="primary", use_container_width=True):
                try:
                    from billing.paystack_handler import initialize_transaction
                    url = initialize_transaction(email, "basic")
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="0; url={url}">
                    <a href="{url}" target="_blank">Click here to complete payment</a>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not initialize payment: {e}")
                    st.info("Make sure PAYSTACK_SECRET_KEY and PAYSTACK_PLAN_CODE_BASIC are set in your .env file.")

    # ── Pro ────────────────────────────────────────────────────────
    with col_pro:
        st.markdown("### 🥇 Pro")
        st.markdown("## $29 / month")
        st.caption("For agencies and growing teams")
        st.divider()

        for f in [
            "✅ Unlimited clients",
            "✅ 5 follow-up attempts",
            "✅ 500 emails per day",
            "✅ Custom follow-up schedule",
            "✅ Activity logs",
            "✅ Gmail integration",
            "✅ AI-written emails (Groq)",
            "✅ Priority support",
        ]:
            st.write(f)

        st.divider()

        if plan == "pro":
            st.success("✅ Current Plan")
            if user.get("paystack_subscription_code"):
                if st.button("Manage Subscription", use_container_width=True, key="manage_pro"):
                    st.info("To cancel or manage your subscription, contact us directly.")
        elif plan == "enterprise":
            st.info("You're on a higher plan.")
        else:
            if st.button("🚀 Subscribe — Pro", type="primary", use_container_width=True):
                try:
                    from billing.paystack_handler import initialize_transaction
                    url = initialize_transaction(email, "pro")
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="0; url={url}">
                    <a href="{url}" target="_blank">Click here to complete payment</a>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not initialize payment: {e}")
                    st.info("Make sure PAYSTACK_SECRET_KEY and PAYSTACK_PLAN_CODE_PRO are set in your .env file.")

    st.divider()

    # ─── Enterprise Card ──────────────────────────────────────────
    st.markdown("### 🏢 Enterprise — Custom Pricing")

    with st.container():
        col1, col2 = st.columns([2, 1])

        with col1:
            st.caption("For large companies with high-volume outreach needs")
            for f in [
                "✅ Unlimited clients",
                "✅ Up to 10 follow-up attempts",
                "✅ Unlimited emails per day — no cap",
                "✅ Custom follow-up schedule",
                "✅ Activity logs",
                "✅ Gmail integration",
                "✅ AI-written emails (Groq)",
                "✅ Dedicated priority support",
                "✅ Custom onboarding & setup",
            ]:
                st.write(f)

        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if plan == "enterprise":
                st.success("✅ Current Plan")
            else:
                st.info("**Pricing negotiated directly.**\n\nContact us to discuss your volume needs and get a custom quote.")
                st.markdown("📧 **tonytechonology@gmail.com**")

    st.divider()

    # ─── Plan comparison table ────────────────────────────────────
    st.subheader("📊 Plan Comparison")

    st.markdown("""
| Feature | Free Trial | Basic | Pro | Enterprise |
|---|---|---|---|---|
| Duration | 2 days | Monthly | Monthly | Custom |
| Max Clients | 50 | 200 | Unlimited | Unlimited |
| Emails Per Day | 50 | 200 | 500 | Unlimited |
| Follow-up Attempts | 1 | 3 | 5 | 10 |
| Custom Schedule | ❌ | ✅ | ✅ | ✅ |
| Priority Support | ❌ | ❌ | ✅ | ✅ |
| Credit Card Required | No | Yes | Yes | Invoice |
""")

    st.divider()

    # ─── FAQ ──────────────────────────────────────────────────────
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
        st.write("Yes. Upgrade anytime from this page. Your new limit takes effect immediately.")

    with st.expander("How does Enterprise pricing work?"):
        st.write("Enterprise is priced based on your volume and needs. "
                 "Contact us directly and we'll set up your account manually "
                 "with a custom plan tailored to your company.")

    with st.expander("Is my Gmail password stored?"):
        st.write("Never. The app uses Google OAuth — only a secure token is stored locally. "
                 "You can revoke access from your Google account at any time.")
