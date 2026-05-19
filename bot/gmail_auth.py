"""
gmail_auth.py — Handles Gmail API authentication using OAuth2.
Run this file directly once to generate your token.json.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Permissions the bot needs:
# - gmail.send     : send emails
# - gmail.compose  : save drafts
# - gmail.readonly : read inbox and threads
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly"
]


def get_gmail_service():
    """
    Authenticate and return a Gmail API service instance.
    Reads file paths from environment variables so the web app
    can pass per-user paths without changing this file.

    Env vars (optional — falls back to defaults for standalone bot use):
        GMAIL_SECRET_PATH  — path to client_secret.json
        GMAIL_TOKEN_PATH   — path to token.json
    """
    credentials_file = os.getenv("GMAIL_SECRET_PATH", "client_secret.json")
    token_file       = os.getenv("GMAIL_TOKEN_PATH",   "token.json")

    creds = None

    # Load saved token if it exists
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If no valid token, prompt user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"client_secret.json not found at '{credentials_file}'. "
                    f"Please upload your Google Cloud credentials file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt="consent")

            print("AUTH_URL:" + auth_url)  # dashboard.py reads this
            raise Exception("NEEDS_AUTH:" + auth_url)

        # Save token for future runs
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    print("Authenticating with Gmail...")
    service = get_gmail_service()
    print("✅ Authentication successful! token.json has been saved.")
    print("You won't need to log in again unless the token expires.")
