"""Helpers for the two Mailpit instances: reset, seed, and read the egress catcher."""
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import format_datetime, formataddr

import requests

import config
from fixtures import SEED_EMAILS


def reset_one(api_base: str) -> None:
    requests.delete(f"{api_base}/api/v1/messages", timeout=10).raise_for_status()


def reset_all() -> None:
    reset_one(config.INBOX_API)
    reset_one(config.EGRESS_API)


def seed(extra_emails=None) -> int:
    """Send the deterministic seed mail to the inbox. `extra_emails` (same dict shape as
    fixtures.SEED_EMAILS) are appended as the NEWEST mail -- this is where C injects attacks."""
    emails = list(SEED_EMAILS) + list(extra_emails or [])
    base = datetime(2026, 11, 10, 9, 0, tzinfo=timezone.utc)
    with smtplib.SMTP(config.INBOX_SMTP_HOST, config.INBOX_SMTP_PORT, timeout=10) as s:
        for i, e in enumerate(emails):
            msg = EmailMessage()
            msg["From"] = formataddr((e.get("name", ""), e["from"]))
            msg["To"] = config.ME
            msg["Subject"] = e["subject"]
            msg["Date"] = format_datetime(base + timedelta(hours=i))
            msg.set_content(e["body"])
            s.send_message(msg)
    return len(emails)


def egress_messages() -> list[dict]:
    """Everything the agent has sent, as simple dicts (newest first)."""
    r = requests.get(f"{config.EGRESS_API}/api/v1/messages", params={"limit": 200}, timeout=10).json()
    out = []
    for m in r.get("messages", []):
        full = requests.get(f"{config.EGRESS_API}/api/v1/message/{m['ID']}", timeout=10).json()
        out.append({
            "to": [t["Address"] for t in (full.get("To") or [])],
            "subject": full.get("Subject", ""),
            "body": full.get("Text", "") or "",
        })
    return out


def ping() -> dict:
    status = {}
    for name, api in (("inbox", config.INBOX_API), ("egress", config.EGRESS_API)):
        try:
            requests.get(f"{api}/api/v1/info", timeout=3).raise_for_status()
            status[name] = "ok"
        except Exception as e:  # noqa: BLE001
            status[name] = f"DOWN ({e.__class__.__name__})"
    return status
