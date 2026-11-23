"""Central configuration. Everything can be overridden with environment variables or a .env file."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # dotenv is optional
    pass

ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / "results"
TRACE_DIR = RESULTS_DIR / "traces"

# --- LLM (DeepSeek, OpenAI-compatible API) ---
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
# deepseek-v4-flash runs with thinking ON by default. For a tool-calling agent we disable it
# (cheaper, faster, and no reasoning_content to pass back). Set DEEPSEEK_THINKING=enabled to turn it on.
THINKING = os.getenv("DEEPSEEK_THINKING", "disabled")

# --- Mailpit ---
INBOX_API = os.getenv("INBOX_API", "http://localhost:8025")
INBOX_SMTP_HOST = os.getenv("INBOX_SMTP_HOST", "localhost")
INBOX_SMTP_PORT = int(os.getenv("INBOX_SMTP_PORT", "1025"))
EGRESS_API = os.getenv("EGRESS_API", "http://localhost:8026")
EGRESS_SMTP_HOST = os.getenv("EGRESS_SMTP_HOST", "localhost")
EGRESS_SMTP_PORT = int(os.getenv("EGRESS_SMTP_PORT", "1026"))

ME = "user@corp.test"
