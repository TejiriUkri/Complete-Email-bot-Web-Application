"""
app.py — Main entry point for the Email Follow-Up Bot web app.
Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="FollowUpBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Session state defaults ───────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ─── Sidebar navigation ───────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/robot.png", width=60)
        st.title("FollowUpBot")
        st.divider()

        if st.session_state.logged_in:
            st.caption(f"👤 {st.session_state.user_email}")

            from auth.user_db import get_plan, trial_days_remaining
            plan = get_plan(st.session_state.user_email)
            if plan == "trial":
                days = trial_days_remaining(st.session_state.user_email)
                st.warning(f"⏳ Trial: {days} days left")
            elif plan == "expired":
                st.error("❌ Plan expired")
            elif plan == "enterprise":
                st.success("🏢 Enterprise Plan")
            else:
                st.success(f"✅ {plan.capitalize()} Plan")

            st.divider()
            pages = {
                "🏠 Dashboard":  "dashboard",
                "⏱️ Schedule":   "schedule",
                "📋 Activity Log": "logs",
                "💳 Pricing":    "pricing",
            }
            for label, key in pages.items():
                if st.button(label, use_container_width=True):
                    st.session_state.page = key
                    st.rerun()

            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.page = "login"
                st.rerun()
        else:
            st.info("Please log in to continue.")


# ─── Page router ─────────────────────────────────────────────────
def main():
    sidebar()

    if not st.session_state.logged_in:
        from views.login import show
        show()
        return

    from auth.user_db import get_plan
    plan = get_plan(st.session_state.user_email)

    if plan == "expired" and st.session_state.page != "pricing":
        st.error("⚠️ Your plan has expired. Please subscribe to continue.")
        st.session_state.page = "pricing"
        from views.pricing import show
        show()
        return

    page = st.session_state.page

    if page == "dashboard":
        from views.dashboard import show
        show()
    elif page == "schedule":
        from views.schedule import show
        show()
    elif page == "logs":
        from views.logs import show
        show()
    elif page == "pricing":
        from views.pricing import show
        show()
    else:
        from views.dashboard import show
        show()


if __name__ == "__main__":
    main()
