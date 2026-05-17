"""
read_csv.py — Loads client data from a CSV or Excel file.

Expected CSV columns:
    name, email, context

Example clients.csv:
    name,email,context
    John Doe,john@example.com,product demo last week
    Jane Smith,jane@example.com,proposal sent on Monday
"""

import csv
import os


def load_clients(filepath: str) -> list[dict]:
    """Load clients from a CSV file and return as a list of dicts."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    clients = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from all fields
            client = {key.strip(): value.strip() for key, value in row.items()}

            # Validate required fields
            if not client.get("email"):
                print(f"⚠️  Skipping row with missing email: {client}")
                continue
            if not client.get("name"):
                client["name"] = client["email"]  # fallback to email if name missing

            clients.append(client)

    print(f"📋 Loaded {len(clients)} clients from {filepath}")
    return clients
