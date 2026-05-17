"""
pages/schedule.py — Let users configure their follow-up timing.
"""

import streamlit as st
from auth.user_db import get_user, get_plan, get_plan_limits, save_settings


def show():
    email  = st.session_state.user_email
    plan   = get_plan(email)
    limits = get_plan_limits(email)
    user   = get_user(email)

    st.title("⏱️ Follow-Up Schedule")
    st.caption("Configure how often your bot follows up with unresponsive clients.")
    st.divider()

    can_customize = limits.get("custom_schedule", False)

    if not can_customize:
        st.warning(
            "⚠️ Custom scheduling is not available on the **Free Trial**. "
            "Upgrade to Basic or Pro to unlock this feature."
        )
        st.info("**Default schedule:** Follow-up on Day 3 after first contact, then stop.")
        if st.button("💳 Upgrade Plan", type="primary"):
            st.session_state.page = "pricing"
            st.rerun()
        return

    current      = user.get("settings", {})
    max_followups = limits.get("max_followups", 3)
    daily_limit   = limits.get("daily_send_limit")   # None = unlimited (Enterprise)

    st.subheader("📅 Follow-Up Timing")
    st.caption("Set how many days to wait before each follow-up attempt.")

    # ─── Follow-up day sliders ────────────────────────────────────
    schedule_defaults = current.get("followup_schedule_days", [3, 7, 14])

    col1, col2 = st.columns(2)
    with col1:
        followup_1 = st.slider(
            "Days before Follow-up #1",
            min_value=1, max_value=14,
            value=schedule_defaults[0] if len(schedule_defaults) > 0 else 3,
            help="Days after the initial email before sending the first follow-up"
        )
    with col2:
        followup_2 = st.slider(
            "Days before Follow-up #2",
            min_value=1, max_value=21,
            value=schedule_defaults[1] if len(schedule_defaults) > 1 else 7,
            disabled=max_followups < 2,
            help="Days after Follow-up #1 before sending the second follow-up"
        )

    followup_3 = 14
    followup_4 = 21
    followup_5 = 30

    if max_followups >= 3:
        followup_3 = st.slider(
            "Days before Follow-up #3",
            min_value=1, max_value=30,
            value=schedule_defaults[2] if len(schedule_defaults) > 2 else 14,
            help="Days after Follow-up #2 before sending the third follow-up"
        )

    # Enterprise gets extra sliders (up to 10 follow-ups)
    if plan == "enterprise":
        st.caption("🏢 Enterprise — configure up to 10 follow-up attempts")
        col3, col4 = st.columns(2)
        with col3:
            followup_4 = st.slider("Days before Follow-up #4", 1, 45,
                value=schedule_defaults[3] if len(schedule_defaults) > 3 else 21)
        with col4:
            followup_5 = st.slider("Days before Follow-up #5", 1, 60,
                value=schedule_defaults[4] if len(schedule_defaults) > 4 else 30)

    st.divider()

    # ─── Other settings ───────────────────────────────────────────
    st.subheader("⚙️ Other Settings")
    col5, col6 = st.columns(2)

    with col5:
        # Daily send limit — Enterprise shows "Unlimited", others show number input
        if daily_limit is None:
            st.info("📧 **Daily Send Limit:** Unlimited (Enterprise)")
            chosen_daily_limit = None
        else:
            chosen_daily_limit = st.number_input(
                "Daily send limit",
                min_value=1,
                max_value=daily_limit,
                value=min(current.get("daily_send_limit", daily_limit), daily_limit),
                help=f"Max emails per day (your plan max: {daily_limit})"
            )

    with col6:
        check_interval = st.selectbox(
            "Inbox check frequency",
            options=[15, 30, 60, 120, 360],
            index=1,
            format_func=lambda x: f"Every {x} minutes" if x < 60 else f"Every {x // 60} hour(s)",
            help="How often the bot checks your inbox for new replies"
        )

    st.divider()

    # ─── Schedule preview ─────────────────────────────────────────
    st.subheader("📋 Schedule Preview")

    if plan == "enterprise":
        schedule = [followup_1, followup_2, followup_3, followup_4, followup_5][:max_followups]
    elif max_followups >= 3:
        schedule = [followup_1, followup_2, followup_3]
    else:
        schedule = [followup_1, followup_2][:max_followups]

    timeline = [("Initial Email", "Day 0", "📤")]
    day = 0
    for i, gap in enumerate(schedule):
        day += gap
        timeline.append((f"Follow-up #{i + 1}", f"Day {day}", "🔁"))
    timeline.append(("Mark as Cold", f"After Day {day}", "❄️"))

    for label, day_label, icon in timeline:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.write(f"{icon} **{label}**")
        with col_b:
            st.write(f"`{day_label}`")

    st.divider()

    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        new_settings = {
            "followup_schedule_days": schedule,
            "max_followups":          max_followups,
            "daily_send_limit":       chosen_daily_limit,
            "check_interval_mins":    check_interval,
        }
        save_settings(email, new_settings)
        st.success("✅ Settings saved successfully!")
