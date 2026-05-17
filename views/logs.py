"""
pages/logs.py — View bot activity logs.
"""

import os
import streamlit as st
from auth.user_db import get_plan

LOG_FILE = "bot_activity.log"


def parse_logs(filepath: str) -> list[dict]:
    """Parse log file into structured list of entries."""
    if not os.path.exists(filepath):
        return []

    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            try:
                # Format: [2026-05-12 10:30:00] MESSAGE
                timestamp = line[1:20]
                message   = line[22:]
                if "ERROR" in message:
                    tag = "error"
                elif "SENT" in message:
                    tag = "sent"
                elif "DRAFT" in message:
                    tag = "draft"
                elif "STOPPED" in message or "STARTED" in message:
                    tag = "system"
                elif "CYCLE" in message:
                    tag = "cycle"
                else:
                    tag = "info"
                entries.append({"timestamp": timestamp, "message": message, "tag": tag})
            except Exception:
                continue

    return list(reversed(entries))  # newest first


def show():
    email = st.session_state.user_email
    plan  = get_plan(email)

    st.title("📋 Activity Log")
    st.caption("Everything your bot has done — emails sent, drafts saved, errors caught.")
    st.divider()

    # ─── Controls ─────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        filter_tag = st.selectbox(
            "Filter by type",
            options=["All", "Sent", "Draft", "Error", "System"],
            index=0
        )
    with col2:
        st.write("")
        st.write("")
        auto_refresh = st.checkbox("Auto-refresh (10s)", value=False)
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Now"):
            st.rerun()

    if auto_refresh:
        import time
        time.sleep(10)
        st.rerun()

    st.divider()

    # ─── Stats row ────────────────────────────────────────────────
    entries = parse_logs(LOG_FILE)

    total_sent   = sum(1 for e in entries if e["tag"] == "sent")
    total_drafts = sum(1 for e in entries if e["tag"] == "draft")
    total_errors = sum(1 for e in entries if e["tag"] == "error")

    c1, c2, c3 = st.columns(3)
    c1.metric("📤 Total Sent",   total_sent)
    c2.metric("📝 Drafts Saved", total_drafts)
    c3.metric("⚠️ Errors",       total_errors)

    st.divider()

    # ─── Log entries ──────────────────────────────────────────────
    if not entries:
        st.info("No activity yet. Start the bot from the Dashboard to see logs here.")
        return

    # Apply filter
    tag_map = {
        "All": None, "Sent": "sent", "Draft": "draft",
        "Error": "error", "System": "system"
    }
    selected_tag = tag_map[filter_tag]
    filtered = [e for e in entries if selected_tag is None or e["tag"] == selected_tag]

    if not filtered:
        st.info(f"No '{filter_tag}' entries found.")
        return

    # Color coding
    colors = {
        "sent":   "🟢",
        "draft":  "🔵",
        "error":  "🔴",
        "system": "⚪",
        "cycle":  "🟡",
        "info":   "⚪",
    }

    for entry in filtered[:200]:   # cap at 200 lines for performance
        icon = colors.get(entry["tag"], "⚪")
        st.markdown(
            f"`{entry['timestamp']}` {icon} {entry['message']}"
        )

    if len(filtered) > 200:
        st.caption(f"Showing latest 200 of {len(filtered)} entries.")

    st.divider()

    if st.button("🗑️ Clear Log File", type="secondary"):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        st.success("Log cleared.")
        st.rerun()
