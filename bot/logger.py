"""
logger.py — Logs all bot activity to a local file with timestamps.
"""

import os
from datetime import datetime

LOG_FILE = "bot_activity.log"


def log(message: str):
    """Write a timestamped log entry to the log file and print it."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(f"📝 LOG: {entry}")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def view_log(last_n: int = 20):
    """Print the last N lines of the log file."""
    if not os.path.exists(LOG_FILE):
        print("No log file found yet.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"\n--- Last {last_n} log entries ---")
    for line in lines[-last_n:]:
        print(line.strip())
