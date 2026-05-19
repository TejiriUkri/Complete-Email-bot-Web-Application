"""
pages/dashboard.py — Main bot control panel.
"""

import os
import time
import threading
import streamlit as st
from auth.user_db import (
    get_user, get_plan, get_plan_limits,
    trial_days_remaining, set_bot_running
)

UPLOAD_DIR = "data/uploads"
STOP_FILE  = "STOP"


def _get_upload_path(email: str) -> str:
    path = os.path.join(UPLOAD_DIR, email.replace("@", "_").replace(".", "_"))
    os.makedirs(path, exist_ok=True)
    return path


def _run_bot_thread(email: str, settings: dict):
    """Runs the bot in a background thread for this user."""
    import sys
    sys.path.insert(0, os.path.abspath("bot"))

    from bot.read_csv import load_clients
    from bot.write_email import create_outreach_email
    from bot.send_email import send_email, save_draft
    from bot.monitor_inbox import (
        get_unanswered_clients, get_replies,
        get_clients_due_for_followup, mark_contacted
    )
    from bot.write_reply import create_reply
    from bot.logger import log
    from bot.daily_counter import can_send, increment, remaining, get_sent_today

    csv_path   = settings.get("csv_path")
    stop_file  = f"STOP_{email.replace('@','_').replace('.','_')}"
    daily_limit = settings.get("daily_send_limit", 50)

    set_bot_running(email, True)
    log(f"BOT STARTED for {email}")

    while True:
        if os.path.exists(stop_file):
            log(f"BOT STOPPED for {email} — kill switch activated.")
            set_bot_running(email, False)
            os.remove(stop_file)
            break

        try:
            clients = load_clients(csv_path)

            # ── Outreach ──────────────────────────────────────────
            if can_send(daily_limit):
                unanswered = get_unanswered_clients(clients)
                for client in unanswered:
                    if not can_send(daily_limit) or os.path.exists(stop_file):
                        break
                    body = create_outreach_email(client)
                    send_email(
                        recipient=client["email"],
                        subject=f"Following up — {client.get('context', 'our conversation')}",
                        message=body
                    )
                    mark_contacted(client["email"], attempt=1)
                    increment()
                    sent_today = get_sent_today()
                    limit_display = str(daily_limit) if daily_limit else "Unlimited"
                    log(f"SENT outreach to {client['name']} <{client['email']}> | Today: {sent_today}/{limit_display}")
                    time.sleep(2)

            # ── Follow-ups ────────────────────────────────────────
            if can_send(daily_limit):
                due = get_clients_due_for_followup(
                    clients,
                    schedule_days=settings["followup_schedule_days"],
                    max_followups=settings["max_followups"]
                )
                for client, attempt_num in due:
                    if not can_send(daily_limit) or os.path.exists(stop_file):
                        break
                    body = create_outreach_email(client)
                    send_email(
                        recipient=client["email"],
                        subject=f"Just checking in — {client.get('context', '')}",
                        message=body
                    )
                    mark_contacted(client["email"], attempt=attempt_num)
                    increment()
                    log(f"SENT follow-up #{attempt_num} to {client['name']} | Today: {get_sent_today()}")
                    time.sleep(2)

            # ── Replies ───────────────────────────────────────────
            replies = get_replies()
            for thread in replies:
                if os.path.exists(stop_file):
                    break
                reply_body = create_reply(thread)
                save_draft(
                    recipient=thread["sender"],
                    subject="Re: " + thread["subject"],
                    message=reply_body
                )
                log(f"DRAFT saved for {thread['sender']}")

        except Exception as e:
            log(f"ERROR for {email}: {e}")

        # Sleep in 30-second chunks, checking kill switch
        interval = settings.get("check_interval_mins", 30) * 60
        for _ in range(interval // 30):
            if os.path.exists(stop_file):
                break
            time.sleep(30)

    set_bot_running(email, False)


def show():
    email = st.session_state.user_email
    user  = get_user(email)
    plan  = get_plan(email)
    limits = get_plan_limits(email)

    st.title("🏠 Dashboard")
    st.caption(f"Logged in as **{email}** · Plan: **{limits.get('label', 'Expired')}**")

    if plan == "trial":
        days = trial_days_remaining(email)
        st.warning(f"⏳ Free trial expires in **{days} days**. [Upgrade now](#)")
    elif plan == "expired":
        st.error("Your plan has expired. Please subscribe to continue.")
        if st.button("Go to Pricing", type="primary"):
            st.session_state.page = "pricing"
            st.rerun()
        return

    st.divider()

    # ─── Status Cards ─────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    bot_running = user.get("bot_running", False)

    with col1:
        status = "🟢 Running" if bot_running else "🔴 Stopped"
        st.metric("Bot Status", status)
    with col2:
        max_c = limits.get("max_clients")
        st.metric("Max Clients", max_c if max_c else "Unlimited")
    with col3:
        daily = limits.get("daily_send_limit")
        st.metric("Emails Per Day", daily if daily else "Unlimited")
    with col4:
        st.metric("Max Follow-ups", limits.get("max_followups", 0))

    st.divider()

    # ─── Section 1: Upload CSV ────────────────────────────────────
    st.subheader("📁 Upload Client List")
    st.caption("CSV must have columns: **name, email, context**")

    upload_path = _get_upload_path(email)
    existing_csv = os.path.join(upload_path, "clients.csv")

    uploaded = st.file_uploader("Choose your CSV file", type=["csv"])
    if uploaded:
        max_clients = limits.get("max_clients")
        import csv, io
        content = uploaded.read().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(content)))

        if max_clients and len(rows) > max_clients:
            st.error(f"Your **{limits['label']}** plan supports up to {max_clients} clients. "
                     f"Your file has {len(rows)}. Please upgrade or trim your list.")
        else:
            with open(existing_csv, "w", encoding="utf-8") as f:
                f.write(content)
            st.success(f"✅ Uploaded {len(rows)} clients successfully.")

    if os.path.exists(existing_csv):
        import pandas as pd
        df = pd.read_csv(existing_csv)
        with st.expander(f"👁️ Preview client list ({len(df)} clients)"):
            st.dataframe(df, use_container_width=True)

    st.divider()

    # ─── Section 2: Gmail Connection ─────────────────────────────
    st.subheader("📧 Gmail Connection")

    token_path = os.path.join(upload_path, "token.json")
    secret_path = os.path.join(upload_path, "client_secret.json")

    if os.path.exists(token_path):
        st.success("✅ Gmail account connected.")
        if st.button("Disconnect Gmail"):
            os.remove(token_path)
            st.rerun()
    else:
        st.info("Upload your **client_secret.json** from Google Cloud Console to connect Gmail.")
        
        # ─── ADDED: Download Guide Segment ────────────────────────
        guide_file_path = "assets/google_setup_guide.docx" # Path to your documentation file
        
        if os.path.exists(guide_file_path):
            with open(guide_file_path, "rb") as file:
                st.download_button(
                    label="📖 Download Google Cloud Setup Guide (PDF)",
                    data=file,
                    file_name="google_setup_guide.docx",
                    mime="application/pdf",
                    help="Click here to download a step-by-step guide on generating your client_secret.json file."
                )
        else:
            # Fallback if the file path hasn't been created yet
            st.caption("ℹ️ Need help? [Click here to view the Google Cloud Console configuration guide](https://console.cloud.google.com/)")
        # ──────────────────────────────────────────────────────────

        secret_file = st.file_uploader("Upload client_secret.json", type=["json"], key="secret_upload")
        if secret_file:
            with open(secret_path, "wb") as f:
                f.write(secret_file.read())
            st.success("✅ Secret uploaded. Click 'Authenticate Gmail' to connect.")

        if os.path.exists(secret_path):
            if st.button("🔗 Authenticate Gmail", type="primary"):
                with st.spinner("Opening browser for Gmail login..."):
                    try:
                        import sys
                        sys.path.insert(0, "bot")
                        # Point auth to user-specific files
                        os.environ["GMAIL_TOKEN_PATH"]  = token_path
                        os.environ["GMAIL_SECRET_PATH"] = secret_path
                        from bot.gmail_auth import get_gmail_service
                        get_gmail_service()
                        st.success("✅ Gmail connected successfully!")
                        st.rerun()
                    except Exception as e:
                        err = str(e)
                        if err.startswith("NEEDS_AUTH:"):
                            auth_url = err.replace("NEEDS_AUTH:", "")
                            st.markdown(f"**Step 1:** [Click here to authorize Gmail]({auth_url})")
                            st.markdown("**Step 2:** Copy the code Google gives you and paste it below:")
                            auth_code = st.text_input("Paste authorization code here")
                            if auth_code and st.button("Submit Code"):
                                try:
                                    from google_auth_oauthlib.flow import InstalledAppFlow
                                    flow = InstalledAppFlow.from_client_secrets_file(secret_path, [
                                        "https://www.googleapis.com/auth/gmail.send",
                                        "https://www.googleapis.com/auth/gmail.compose",
                                        "https://www.googleapis.com/auth/gmail.readonly"
                                    ])
                                    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                                    flow.fetch_token(code=auth_code)
                                    creds = flow.credentials
                                    with open(token_path, "w") as f:
                                        f.write(creds.to_json())
                                    st.success("✅ Gmail connected successfully!")
                                    st.rerun()
                                except Exception as e2:
                                    st.error(f"Failed: {e2}")
                        else:
                            st.error(f"Authentication failed: {e}")
    st.divider()

    # ─── Section 3: Bot Controls ──────────────────────────────────
    st.subheader("🤖 Bot Controls")

    gmail_ready = os.path.exists(token_path)
    csv_ready   = os.path.exists(existing_csv)

    if not gmail_ready:
        st.warning("⚠️ Connect your Gmail account before starting the bot.")
    if not csv_ready:
        st.warning("⚠️ Upload your client CSV before starting the bot.")

    col_start, col_stop = st.columns(2)

    with col_start:
        start_disabled = bot_running or not gmail_ready or not csv_ready
        if st.button("▶️ Start Bot", type="primary", use_container_width=True, disabled=start_disabled):
            settings = user.get("settings", {})
            settings["csv_path"] = existing_csv
            settings["daily_send_limit"] = limits.get("daily_send_limit", 10)
            settings["max_followups"]    = limits.get("max_followups", 1)

            thread = threading.Thread(
                target=_run_bot_thread,
                args=(email, settings),
                daemon=True
            )
            thread.start()
            set_bot_running(email, True)
            st.success("🟢 Bot started! It will run in the background.")
            st.rerun()

    with col_stop:
        stop_file = f"STOP_{email.replace('@','_').replace('.','_')}"
        if st.button("⏹️ Stop Bot", use_container_width=True, disabled=not bot_running):
            with open(stop_file, "w") as f:
                f.write("stop")
            st.warning("🛑 Stop signal sent. Bot will finish its current task and shut down.")
            st.rerun()

    if bot_running:
        st.info("🟢 Your bot is actively running. Check the **Activity Log** to see what it's doing.")