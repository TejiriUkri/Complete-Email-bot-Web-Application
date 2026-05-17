"""
monitor_inbox.py — Checks Gmail inbox for client replies and manages follow-up tracking.
"""

import os
import json
import base64
from datetime import datetime, timedelta
from gmail_auth import get_gmail_service

TRACKER_FILE = "follow_up_tracker.json"


# ─── TRACKER HELPERS ─────────────────────────────────────────────

def load_tracker() -> dict:
    """Load the follow-up tracker from disk. Creates it if it doesn't exist."""
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    return {}


def save_tracker(tracker: dict):
    """Save the follow-up tracker to disk."""
    with open(TRACKER_FILE, "w") as f:
        json.dump(tracker, f, indent=2)


def mark_contacted(email: str, attempt: int):
    """
    Record that a client was contacted.
    Stores the attempt number and timestamp of last contact.
    """
    tracker = load_tracker()
    tracker[email.lower()] = {
        "last_contacted": datetime.now().isoformat(),
        "attempt": attempt
    }
    save_tracker(tracker)


def mark_replied(email: str):
    """Mark a client as having replied — they won't receive more follow-ups."""
    tracker = load_tracker()
    tracker[email.lower()] = {
        "last_contacted": datetime.now().isoformat(),
        "attempt": "replied"  # special flag — no more follow-ups
    }
    save_tracker(tracker)


def get_clients_due_for_followup(
    clients: list[dict],
    schedule_days: list[int],
    max_followups: int
) -> list[tuple]:
    """
    Returns a list of (client, next_attempt_number) tuples for clients
    who haven't replied and enough days have passed since last contact.
    """
    tracker = load_tracker()
    replied_emails = _get_replied_emails()
    due = []

    for client in clients:
        email = client["email"].strip().lower()

        # Skip if client has already replied
        if email in replied_emails:
            continue

        record = tracker.get(email)

        # Skip if never contacted (outreach handles that separately)
        if not record:
            continue

        # Skip if already replied (flagged in tracker)
        if record.get("attempt") == "replied":
            continue

        current_attempt = record.get("attempt", 0)

        # Skip if max follow-ups reached
        if current_attempt >= max_followups:
            continue

        last_contacted = datetime.fromisoformat(record["last_contacted"])
        days_since = (datetime.now() - last_contacted).days
        days_to_wait = schedule_days[current_attempt - 1] if current_attempt > 0 else schedule_days[0]

        if days_since >= days_to_wait:
            next_attempt = current_attempt + 1
            due.append((client, next_attempt))

    print(f"🔁 {len(due)} clients due for follow-up.")
    return due


def _get_replied_emails() -> set:
    """Get set of email addresses that have replied to us."""
    service = get_gmail_service()
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=200
    ).execute()

    messages = results.get("messages", [])
    replied = set()

    for msg in messages:
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From"]
        ).execute()

        headers = detail.get("payload", {}).get("headers", [])
        for header in headers:
            if header["name"] == "From":
                raw = header["value"]
                email = raw.split("<")[1].replace(">", "").strip().lower() if "<" in raw else raw.strip().lower()
                replied.add(email)

    return replied


# ─── INBOX FUNCTIONS ─────────────────────────────────────────────

def get_unanswered_clients(clients: list[dict]) -> list[dict]:
    """
    Returns clients who have never been contacted before.
    Checks both the tracker file and inbox replies.
    """
    tracker = load_tracker()
    replied_emails = _get_replied_emails()

    unanswered = []
    for client in clients:
        email = client["email"].strip().lower()
        already_contacted = email in tracker
        already_replied = email in replied_emails

        if not already_contacted and not already_replied:
            unanswered.append(client)

    print(f"📊 {len(unanswered)} new clients to contact out of {len(clients)} total.")
    return unanswered


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from email payload."""
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            body += _extract_body(part)
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return body


PROCESSED_FILE = "processed_messages.json"


def _load_processed() -> set:
    """Load the set of already-processed message IDs from disk."""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()


def _mark_message_processed(message_id: str):
    """Record a message ID so the bot never processes it again."""
    processed = _load_processed()
    processed.add(message_id)
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed), f)


def get_replies() -> list[dict]:
    """
    Fetch ONLY new, unprocessed client replies from the inbox.
    - Skips messages already processed in a previous cycle
    - Skips emails sent by ourselves
    - Marks each processed message immediately so next cycle ignores it
    - Marks replying clients in tracker so follow-ups stop for them
    """
    service   = get_gmail_service()
    processed = _load_processed()
    own_email = os.getenv("SENDER_EMAIL", "").lower()

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=20
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("✅ No new replies to process.")
        return []

    threads = []

    for msg in messages:
        message_id = msg["id"]

        # ── Skip if already handled in a previous cycle ────────
        if message_id in processed:
            continue

        detail = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        headers     = detail.get("payload", {}).get("headers", [])
        header_dict = {h["name"]: h["value"] for h in headers}

        sender    = header_dict.get("From", "")
        subject   = header_dict.get("Subject", "(no subject)")
        thread_id = detail.get("threadId")

        # Extract plain email address from "Name <email>" format
        if "<" in sender:
            sender_email = sender.split("<")[1].replace(">", "").strip().lower()
        else:
            sender_email = sender.strip().lower()

        # ── Skip our own sent emails appearing in inbox ─────────
        if sender_email == own_email:
            _mark_message_processed(message_id)
            continue

        # Stop future follow-ups to this client since they replied
        mark_replied(sender_email)

        # Get the full thread so AI has conversation context
        thread_data = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="full"
        ).execute()

        history = []
        for thread_msg in thread_data.get("messages", []):
            t_headers = {h["name"]: h["value"] for h in thread_msg.get("payload", {}).get("headers", [])}
            from_addr = t_headers.get("From", "")
            body      = _extract_body(thread_msg.get("payload", {}))
            role      = "me" if own_email in from_addr.lower() else "client"
            history.append({"role": role, "content": body.strip()})

        threads.append({
            "sender":     sender,
            "subject":    subject,
            "thread_id":  thread_id,
            "message_id": message_id,
            "history":    history
        })

        # ── Mark processed immediately so next cycle skips it ──
        _mark_message_processed(message_id)

    if threads:
        print(f"💬 {len(threads)} new unprocessed repl{'y' if len(threads) == 1 else 'ies'} found.")
    else:
        print("✅ No new replies to process.")

    return threads

