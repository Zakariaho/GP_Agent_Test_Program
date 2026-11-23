"""The four agent tools, implemented over the Mailpit REST API (read) and SMTP (send)."""
import re
import smtplib
from email.message import EmailMessage

import requests

import config


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def list_emails(limit: int = 10) -> list[dict]:
    r = requests.get(f"{config.INBOX_API}/api/v1/messages", params={"limit": limit}, timeout=10).json()
    return [{"id": m["ID"], "from": m["From"]["Address"], "subject": m["Subject"], "date": m["Created"]}
            for m in r.get("messages", [])]


def read_email(id: str) -> dict:
    m = requests.get(f"{config.INBOX_API}/api/v1/message/{id}", timeout=10)
    m.raise_for_status()
    m = m.json()
    body = m.get("Text") or _strip_html(m.get("HTML", ""))
    return {"id": id, "from": m["From"]["Address"], "subject": m["Subject"], "body": body}


def _send(to: str, subject: str, body: str) -> dict:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = config.ME, to, subject
    msg.set_content(body)
    with smtplib.SMTP(config.EGRESS_SMTP_HOST, config.EGRESS_SMTP_PORT, timeout=10) as s:
        s.send_message(msg)
    return {"status": "sent", "to": to}


def reply(id: str, body: str) -> dict:
    m = read_email(id)
    return _send(m["from"], "Re: " + m["subject"], body)


def forward(id: str, to: str, note: str = "") -> dict:
    m = read_email(id)
    return _send(to, "Fwd: " + m["subject"], f"{note}\n\n--- Forwarded message ---\n{m['body']}")


TOOLS = {"list_emails": list_emails, "read_email": read_email, "reply": reply, "forward": forward}

# OpenAI-style function schemas (DeepSeek uses the same format)
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "list_emails",
        "description": "List emails in the user's inbox, newest first. Returns id, from, subject, date.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Max emails to return (default 10)"}}}}},
    {"type": "function", "function": {
        "name": "read_email",
        "description": "Read the full body of one email by id.",
        "parameters": {"type": "object", "properties": {
            "id": {"type": "string", "description": "Email id from list_emails"}}, "required": ["id"]}}},
    {"type": "function", "function": {
        "name": "reply",
        "description": "Send a reply to the sender of an email. Only use when the user explicitly asks to reply.",
        "parameters": {"type": "object", "properties": {
            "id": {"type": "string", "description": "Id of the email being replied to"},
            "body": {"type": "string", "description": "Reply text"}}, "required": ["id", "body"]}}},
    {"type": "function", "function": {
        "name": "forward",
        "description": "Forward an email to another address. Only use when the user explicitly asks to forward.",
        "parameters": {"type": "object", "properties": {
            "id": {"type": "string", "description": "Id of the email to forward"},
            "to": {"type": "string", "description": "Recipient email address"},
            "note": {"type": "string", "description": "Optional note placed above the forwarded text"}},
            "required": ["id", "to"]}}},
]
