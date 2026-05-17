"""
pages/login.py — Login and signup page.
"""

import streamlit as st
from auth.user_db import register_user, login_user, trial_days_remaining


def show():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/robot.png", width=72)
        st.title("FollowUpBot")
        st.caption("AI-powered email follow-up automation")
        st.divider()

        tab_login, tab_signup = st.tabs(["🔐 Login", "🆕 Sign Up"])

        # ─── Login Tab ────────────────────────────────────────────
        with tab_login:
            st.subheader("Welcome back")
            email = st.text_input("Email address", key="login_email", placeholder="you@gmail.com")
            password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

            if st.button("Login", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    success, msg = login_user(email, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_email = email.strip().lower()
                        st.session_state.page = "dashboard"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # ─── Signup Tab ───────────────────────────────────────────
        with tab_signup:
            st.subheader("Create your account")
            st.info("🎉 Start with a **2-day free trial** — no credit card required.")

            new_email = st.text_input("Email address", key="signup_email", placeholder="you@gmail.com")
            new_password = st.text_input("Password", type="password", key="signup_password", placeholder="Min 6 characters")
            confirm_password = st.text_input("Confirm password", type="password", key="confirm_password", placeholder="Repeat password")

            if st.button("Create Account", use_container_width=True, type="primary"):
                if not new_email or not new_password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, msg = register_user(new_email, new_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_email = new_email.strip().lower()
                        st.session_state.page = "dashboard"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        st.divider()
        st.caption("By signing up you agree to our Terms of Service.")
