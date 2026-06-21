"""Central config. Everything tunable lives here so you change one place on demo day."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- HydraDB scoping ---
# tenant_id  = the app  |  sub_tenant_id = the user. For the demo we hardcode one user.
TENANT_ID = os.getenv("GOBLIN_TENANT_ID", "the-goblin")
USER_ID = os.getenv("GOBLIN_USER_ID", "rohit")

# --- Keys (app still runs in offline mode if these are blank) ---
HYDRA_DB_API_KEY = os.getenv("HYDRA_DB_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "").strip()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

# --- Nebius Token Factory (OpenAI-compatible) ---
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
# Fast, capable instruct model for JSON extraction. Override to taste, e.g.
#   Qwen/Qwen3-30B-A3B-Instruct-2507   (fast MoE alt)
#   deepseek-ai/DeepSeek-V3.2-fast     (strong alt)
NEBIUS_MODEL = os.getenv("NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

# Which LLM powers the agent's brain. Auto-picks Nebius (free credits) if its key
# is present, else Anthropic, else neither (deterministic fallback). Force with
# LLM_PROVIDER=nebius|anthropic|none.
def _resolve_provider():
    forced = os.getenv("LLM_PROVIDER", "").strip().lower()
    if forced in ("nebius", "anthropic", "none"):
        return forced
    if NEBIUS_API_KEY:
        return "nebius"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    return "none"

LLM_PROVIDER = _resolve_provider()

# --- Demo time anchor ---
# All "N days ago" math is relative to THIS fixed date, not the real clock, so the
# story ("17 days ignored") stays identical on demo day. Seed data uses day-offsets.
DEMO_NOW = "2026-06-21"

# --- Pattern taxonomy (keep to 4 for reliable detection) ---
PATTERN_COLORS = {
    "ghosting": "purple",
    "broken_promise": "yellow",
    "bad_excuse": "red",
    "transactional": "blue",
}
PATTERN_LABELS = {
    "ghosting": "Ghosting",
    "broken_promise": "Broken Promise",
    "bad_excuse": "Bad Excuse",
    "transactional": "Transactional",
}
SEVERITY_WEIGHT = {"low": 12, "medium": 22, "high": 34}
