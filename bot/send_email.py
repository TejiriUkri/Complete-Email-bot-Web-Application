"""
send_email.py — Handles sending emails and saving drafts via the Gmail API.
"""

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from gmail_auth import get_gmail_service
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")


def _build_mime_message(recipient: str, subject: str, message: str):
    """Build a MIME email message."""
    mime_msg = MIMEMultipart()
    mime_msg["From"] = SENDER_EMAIL
    mime_msg["To"] = recipient
    mime_msg["Subject"] = subject
    # Convert newlines to HTML line breaks for proper formatting
    html_body = message.replace("\n", "<br>")
    mime_msg.attach(MIMEText(html_body, "html"))
    return mime_msg


def send_email(recipient: str, subject: str, message: str):
    """Send an email immediately via Gmail API."""
    service = get_gmail_service()
    mime_msg = _build_mime_message(recipient, subject, message)

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
    body = {"raw": raw}

    sent = service.users().messages().send(userId="me", body=body).execute()
    print(f"✅ Email sent to {recipient} | Message ID: {sent['id']}")
    return sent


def save_draft(recipient: str, subject: str, message: str):
    """Save an email as a Gmail Draft instead of sending immediately."""
    service = get_gmail_service()
    mime_msg = _build_mime_message(recipient, subject, message)

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
    body = {"message": {"raw": raw}}

    draft = service.users().drafts().create(userId="me", body=body).execute()
    print(f"📝 Draft saved for {recipient} | Draft ID: {draft['id']}")
    return draft
