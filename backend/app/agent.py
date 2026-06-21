"""The 'brain': Claude calls for the two things that must feel intelligent —
extracting dark patterns from raw conversation, and writing the context-aware
repair suggestion. Both have deterministic fallbacks so a bad/empty Claude
response never breaks the demo (the seed answer_key is the safety net).
"""
import json

from . import config

# --- Build whichever LLM client the resolved provider needs ---------------
_provider = config.LLM_PROVIDER
_nebius = None
_anthropic = None

if _provider == "nebius":
    try:
        from openai import OpenAI  # Nebius is OpenAI-compatible
        _nebius = OpenAI(base_url=config.NEBIUS_BASE_URL, api_key=config.NEBIUS_API_KEY)
    except Exception:
        _provider = "none"
elif _provider == "anthropic":
    try:
        import anthropic  # type: ignore
        _anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    except Exception:
        _provider = "none"


def provider():
    """Which brain is live: 'nebius' (model id) | 'anthropic' | 'none' (fallback)."""
    if _provider == "nebius":
        return f"nebius:{config.NEBIUS_MODEL}"
    return _provider


def claude_on():
    """Back-compat for callers/UI: is ANY real LLM live (not just the fallback)?"""
    return _provider != "none"


def _ask_json(system, user, max_tokens=1024):
    """Ask the active LLM for JSON. Returns parsed dict or None on any failure
    (callers fall back to the deterministic answer key)."""
    try:
        if _provider == "nebius":
            resp = _nebius.chat.completions.create(
                model=config.NEBIUS_MODEL,
                max_tokens=max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
            )
            text = resp.choices[0].message.content or ""
        elif _provider == "anthropic":
            msg = _anthropic.messages.create(
                model=config.CLAUDE_MODEL, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        else:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1].lstrip("json").strip()
        return json.loads(text)
    except Exception:
        return None


# --------------------------------------------------------------------------
# 1) EXTRACTION: conversation -> coins
# --------------------------------------------------------------------------
EXTRACT_SYS = """You audit a chat log between the USER and ONE contact and flag the USER's
relationship "dark patterns". Judge ONLY the user's behavior, never the contact's.

Lines are tagged "(day -N)" meaning sent N days ago. Today is day 0. Bigger N = older.

The ONLY four pattern types:
- ghosting: the contact sent the most recent message and the USER left it unanswered
  for many days (a long silent gap where the user went quiet). Age = days since that
  unanswered message.
- broken_promise: the USER explicitly promised something ("I'll send X", "let's do Y")
  and did not deliver, or re-promised without delivering. Age = days since first promise.
- bad_excuse: the USER offered a weak/evasive excuse instead of doing the thing.
- transactional: nearly every message FROM the user is an ask/request, with little or no
  reciprocity (an extractive relationship). Age = days since the pattern began.

Rules:
- A HEALTHY conversation (balanced, responsive, promises kept) has NO patterns: return {"coins": []}.
- At most ONE pattern per conversation: the single dominant one.
- TIE-BREAKER: if the contact sent the most recent message and the user never replied,
  it is GHOSTING (even if a promise was also involved). Silence outweighs the promise.
- severity: high = clear + costly, medium = real but fixable, low = mild.

Return ONLY JSON, no prose:
{"coins":[{"pattern":"<type>","severity":"low|medium|high","age_days":<int>,"summary":"<one sentence about the user>","evidence":["<fact>","<fact>"]}]}

Examples:
Conversation:
(day -20) Bob: you still owe me that playlist haha
(day -3) Bob: any chance? no worries if not
=> {"coins":[{"pattern":"ghosting","severity":"medium","age_days":20,"summary":"User left Bob's messages unanswered for 20 days.","evidence":["Bob sent the last messages","No reply from the user for 20 days"]}]}

Conversation:
(day -2) Kim: thanks for lunch, that was lovely
(day -2) user: anytime! same time next week?
(day -1) Kim: yes please
=> {"coins":[]}"""


def extract_patterns(contact, messages, fallback_coins):
    """Return list of coin dicts. Falls back to the seed answer key."""
    convo = "\n".join(f"(day -{m['day']}) {m['sender']}: {m['text']}" for m in messages)
    data = _ask_json(EXTRACT_SYS, f"Contact: {contact}\nConversation:\n{convo}\n\nReturn the JSON now.")
    coins = (data or {}).get("coins")
    if not isinstance(coins, list):
        return [dict(c) for c in fallback_coins]  # safety net
    # validate each coin minimally; drop anything malformed
    clean = []
    for c in coins:
        if not isinstance(c, dict):
            continue
        if c.get("pattern") not in config.PATTERN_COLORS:
            continue
        c.setdefault("age_days", 0)
        c.setdefault("summary", f"{c['pattern']} with {contact}")
        c.setdefault("evidence", [])
        c["severity"] = _severity_for(c["pattern"], c.get("age_days", 0), c.get("severity"))
        clean.append(c)
    return clean or [dict(c) for c in fallback_coins]


def _severity_for(pattern, age_days, model_severity):
    """Don't trust the model's subjective severity for time-based patterns: an
    old ghost / broken promise is objectively worse. Keep the model's call for
    transactional/bad_excuse where age is less meaningful."""
    if pattern in ("ghosting", "broken_promise"):
        if age_days >= 14:
            return "high"
        if age_days >= 6:
            return "medium"
        return "low"
    return model_severity if model_severity in config.SEVERITY_WEIGHT else "medium"


# --------------------------------------------------------------------------
# 2) SUGGESTION: recalled memory -> personalized repair (the context-aware step)
# --------------------------------------------------------------------------
SUGGEST_SYS = """You are a relationship repair coach. Given a detected pattern and the
user's REMEMBERED history with this person (tone, what repair worked before), produce a
short, personalized repair. Use the memory: match their preferred tone, avoid what failed.
Return ONLY JSON:
{"prediction":"<what happens if ignored>","smallest_action":"<one tiny action>","suggested_message":"<a ready-to-send message in the user's voice>","why_personalized":"<one line citing the remembered context>"}"""


def suggest_repair(coin, contact, memory_snippets):
    memory = "\n".join(f"- {s}" for s in memory_snippets) or "- (no prior memory found)"
    user = (f"Contact: {contact}\nPattern: {coin.get('pattern')}\n"
            f"Evidence: {coin.get('evidence')}\nRemembered context:\n{memory}")
    data = _ask_json(SUGGEST_SYS, user)
    if isinstance(data, dict) and data.get("suggested_message"):
        return data
    return _fallback_suggestion(coin, contact, memory_snippets)


def _fallback_suggestion(coin, contact, memory_snippets):
    pattern = coin.get("pattern", "ghosting")
    cited = next((s for s in memory_snippets if contact.lower() in s.lower()), "")
    templates = {
        "ghosting": {
            "prediction": "In a few more days this stops being a normal reply and turns into an apology.",
            "smallest_action": "Send one honest acknowledgement, no excuse.",
            "suggested_message": f"Hey {contact} — I went quiet on this, sorry. Still up for it this week?",
        },
        "broken_promise": {
            "prediction": "Re-promising again without delivering will cost real trust.",
            "smallest_action": "Deliver the thing or give a real date, nothing else.",
            "suggested_message": f"{contact}, sending it by end of day today — no more 'tomorrow'.",
        },
        "bad_excuse": {
            "prediction": "Another long excuse reads worse than a short truth.",
            "smallest_action": "Drop the excuse, just answer.",
            "suggested_message": f"Hey {contact}, no good excuse — here's where things actually stand:",
        },
        "transactional": {
            "prediction": "One more ask without a give-back tips this into extractive.",
            "smallest_action": "Send a no-ask message that gives value.",
            "suggested_message": f"Hey {contact}, no ask this time — saw this and thought of you:",
        },
    }
    t = templates.get(pattern, templates["ghosting"])
    return {**t, "why_personalized": (f"Based on remembered context: {cited}" if cited else
                                      "Generic repair (no memory matched).")}


# --------------------------------------------------------------------------
# 3) PREDICTION: deterministic, fast, demo-safe (no LLM in the hot path)
# --------------------------------------------------------------------------
def predict(contact, open_coins):
    """Glowing-coin prediction. Simple rules over the coins we remember."""
    if not open_coins:
        return None
    worst = max(open_coins, key=lambda c: c.get("age_days", 0))
    pattern = worst.get("pattern", "ghosting")
    age = worst.get("age_days", 0)
    return {
        "pattern": pattern,
        "color": config.PATTERN_COLORS.get(pattern, "gray"),
        "reason": f"You have an open {config.PATTERN_LABELS.get(pattern, pattern)} loop "
                  f"with {contact} that's {age} days old and unaddressed.",
        "repairable": age < 21,
    }
