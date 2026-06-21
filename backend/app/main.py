"""The Goblin backend API.

Flow:  POST /ingest  (agent reads convos, writes coins+profiles to HydraDB)
       GET  /dashboard (derive Tamagotchis + Goblin from recalled coins)
       GET  /coin?id=  (inspector: recall memory -> personalized repair)
       POST /repair    (write resolution memory -> coin removed, Goblin shrinks)
       GET  /trace     (HydraDB write/query log = the proof panel)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config, agent, adapters
from .hydra import db, TRACE, MIRROR, PROFILES, LEARNED
from .patterns import tamagotchi_state, goblin_stage, decorate_coin
from .seed import SEED, contact_names

app = FastAPI(title="The Goblin", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    db.ensure_tenant()


def _cid(contact):
    return contact.lower()


def _open_coins():
    return [c for c in MIRROR.values() if c.get("status") != "resolved"]


# ---------------------------------------------------------------- meta
@app.get("/")
def root():
    return {
        "app": "The Goblin",
        "mode": db.mode,
        "llm": agent.provider(),
        "endpoints": ["/ingest", "/dashboard", "/coin?id=", "/repair", "/trace", "/reset"],
    }


@app.get("/health")
def health():
    return {"ok": True, "mode": db.mode, "llm": agent.provider()}


# ---------------------------------------------------------------- ingest
def _store_conversation(contact, relationship_type, profile, messages, answer_key):
    """Shared pipeline: write the relationship profile, detect coins, write coins.
    Used by both /ingest (seed) and /ingest_raw (real chats)."""
    ptext = (f"{contact}: {relationship_type}. Prefers {profile.get('tone','')}. "
             f"Repairs best with {profile.get('repair_strategy','')}. {profile.get('note','')}")
    db.write_memory(ptext, f"{_cid(contact)}::profile",
                    {"kind": "profile", "contact": contact,
                     "tone": profile.get("tone", ""),
                     "repair_strategy": profile.get("repair_strategy", "")})

    created = []
    coins = agent.extract_patterns(contact, messages, answer_key)
    for c in coins:
        sid = f"{_cid(contact)}::{c['pattern']}"
        meta = decorate_coin({
            "kind": "coin", "contact": contact, "pattern": c["pattern"],
            "severity": c.get("severity", "medium"), "age_days": c.get("age_days", 0),
            "status": "open", "summary": c.get("summary", ""),
            "evidence": c.get("evidence", []),
        })
        db.write_memory(c.get("summary", ""), sid, meta)
        created.append(sid)
    return created


@app.post("/ingest")
def ingest():
    """Session 1: the agent reads each SEEDED conversation, extracts coins, and
    writes them + the relationship profile into HydraDB."""
    created = []
    for contact, data in SEED.items():
        created += _store_conversation(contact, data["relationship_type"],
                                       data["profile"], data["messages"], data["answer_key"])
    return {"mode": db.mode, "claude": agent.claude_on(),
            "coins_created": created, "count": len(created)}


class IngestRawIn(BaseModel):
    text: str
    your_name: str = "me"      # which sender label is you
    source: str = "auto"       # "auto" (LLM normalizes) | "whatsapp" (fast parser)


@app.post("/ingest_raw")
def ingest_raw(body: IngestRawIn):
    """Ingest a REAL chat (WhatsApp export or any pasted log). Normalizes it to the
    same shape as the seed, then runs the identical detect -> store pipeline."""
    contact = messages = profile = None
    rel = "contact"

    if body.source == "whatsapp":
        parsed = adapters.parse_whatsapp(body.text, you_names=(body.your_name, "me", "you"))
        if parsed:
            contact, messages = parsed
            profile = {"tone": "concise and honest", "repair_strategy": "a short honest message"}

    if messages is None:  # auto path, or WhatsApp parse didn't match -> LLM normalize
        norm = agent.normalize_chat(body.text, body.your_name)
        if not norm:
            raise HTTPException(422, "couldn't parse this chat (free-form paste needs an LLM key)")
        contact, messages = norm["contact"], norm["messages"]
        profile, rel = norm["profile"], norm["relationship_type"]

    created = _store_conversation(contact, rel, profile, messages, answer_key=[])
    return {"mode": db.mode, "contact": contact, "messages_parsed": len(messages),
            "coins_created": created, "count": len(created)}


# ---------------------------------------------------------------- dashboard
@app.get("/dashboard")
def dashboard():
    """Session 2: derive the whole world from a real HydraDB recall.
    On a cold start the mirror is empty, so this rebuilds purely from memory."""
    db.recall("all open relationship dark patterns and coins for the user", max_results=50)

    contacts = []
    for name in contact_names():
        ccoins = [c for c in _open_coins() if c.get("contact") == name]
        score, state, warning = tamagotchi_state(ccoins)
        pred = agent.predict(name, ccoins)
        contacts.append({
            "name": name,
            "relationship_type": SEED[name]["relationship_type"],
            "score": score, "state": state, "warning": warning,
            "open_coin_count": len(ccoins),
            "main_pattern": ccoins[0]["pattern"] if ccoins else None,
            "predicted": pred,
        })

    open_all = _open_coins()
    return {
        "mode": db.mode,
        "goblin": goblin_stage(len(open_all)),
        "contacts": contacts,
        "coins": [decorate_coin(dict(c)) for c in open_all],
        "trace_count": len(TRACE),
    }


# ---------------------------------------------------------------- inspector
@app.get("/coin")
def coin_inspector(id: str):
    """Click a coin: recall this person's memory and produce a personalized repair."""
    coin = MIRROR.get(id)
    if not coin:
        db.recall(f"coin {id}", max_results=50)
        coin = MIRROR.get(id)
    if not coin:
        raise HTTPException(404, f"coin '{id}' not found")

    contact = coin.get("contact", "")
    snippets = db.recall_text(f"history, tone and past repairs with {contact}", max_results=10)
    learned = db.learned_for(contact)               # what worked in PAST repairs
    s = agent.suggest_repair(coin, contact, learned + snippets)

    return {
        "coin": decorate_coin(dict(coin)),
        "evidence": coin.get("evidence", []),
        "retrieved_memory": snippets,           # show this in UI = proof recall shaped the answer
        "learned_from_past": learned,           # past-repair rules that altered this recommendation
        "prediction": s.get("prediction"),
        "smallest_action": s.get("smallest_action"),
        "suggested_message": s.get("suggested_message"),
        "why_personalized": s.get("why_personalized"),
    }


# ---------------------------------------------------------------- repair
class RepairIn(BaseModel):
    coin_id: str


@app.post("/repair")
def repair(body: RepairIn):
    """Complete a repair: write a resolution memory. Coin resolves, Goblin shrinks,
    and next session the agent REMEMBERS this and won't re-flag it."""
    coin = MIRROR.get(body.coin_id)
    if not coin:
        raise HTTPException(404, f"coin '{body.coin_id}' not found")

    contact = coin.get("contact", "")
    pattern = coin.get("pattern", "")
    learned = SEED.get(contact, {}).get("profile", {}).get("repair_strategy", "a short honest message")
    text = (f"User repaired the {pattern} with {contact} on {config.DEMO_NOW}. "
            f"Outcome: positive. Learned rule: {learned} works with {contact}.")
    # The repair memory's existence IS the resolution record. We can't mutate the
    # coin (HydraDB upsert won't update metadata on an existing source_id), so on
    # recall we treat a coin as resolved when its '::repair' memory is present.
    db.write_memory(text, f"{body.coin_id}::repair",
                    {"kind": "repair", "contact": contact, "resolves": body.coin_id,
                     "learned_rule": f"{learned} works with {contact}"})

    ccoins = [c for c in _open_coins() if c.get("contact") == contact]
    score, state, warning = tamagotchi_state(ccoins)
    return {
        "resolved": body.coin_id,
        "goblin": goblin_stage(len(_open_coins())),
        "contact": {"name": contact, "score": score, "state": state, "warning": warning},
    }


# ---------------------------------------------------------------- trace / reset
@app.get("/trace")
def trace():
    return {"mode": db.mode, "lines": TRACE}


@app.post("/reset")
def reset(hard: bool = False):
    """Demo convenience. Soft (default): wipe the in-process cache + trace, but
    leave HydraDB intact (so the NEXT load proves cross-session recall).
    Hard (?hard=true): also delete all memories from HydraDB for a clean re-run."""
    deleted = db.purge() if hard else None
    MIRROR.clear()
    PROFILES.clear()
    LEARNED.clear()
    TRACE.clear()
    return {"ok": True, "hard": hard, "deleted_from_hydradb": deleted}
