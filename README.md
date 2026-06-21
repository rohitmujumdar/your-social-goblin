# The Social Goblin 🪙👹

A relationship-maintenance mini-game. Each contact is a Tamagotchi whose health
reflects the relationship. Detected "dark patterns" (ghosting, broken promises,
bad excuses, transactional behavior) become colored **coins** that a **Goblin**
collects. The Goblin grows heavier as your unresolved patterns pile up. Fix a
relationship and the coin vanishes, the Goblin shrinks, the Tamagotchi heals.

Built for the **"Agents you Love" hackathon** (theme: *Context over Amnesia*).
**HydraDB** is the memory brain; an LLM does the pattern-detection + repair logic.
The LLM provider is pluggable and defaults to **Nebius Token Factory** (free
credits, OpenAI-compatible); Anthropic Claude is the drop-in alternative.

## The pitch in one line

> The Goblin feeds on the parts of your relationships you refuse to repair.
> Every coin is a memory in HydraDB; close the tab and reopen — it remembers,
> predicts your next pattern, and adapts after you repair one.

---

## How memory works (the part judges score)

- **Every coin = one memory written to HydraDB.** Nothing about the dashboard is
  stored as app state. Tamagotchi health, the Goblin's size, and warnings are all
  **derived fresh** from a HydraDB recall on every `/dashboard` call.
- **Cross-session proof:** restart the backend (= new session). The in-process
  cache is empty, so `/dashboard` rebuilds the entire world from a real HydraDB
  recall.
- **Context-aware execution:** `/coin` recalls a contact's *profile* + past
  *repairs* and personalizes the suggested message ("Marc responds to short
  honesty, skip the long excuse").
- **It evolves:** `/repair` writes a resolution memory, so next session the agent
  remembers Marc was fixed and stops flagging him.
- **The proof panel:** every HydraDB write/query is logged to `/trace` — that's
  the required "execution logs," ready to render as a terminal panel.

---

## Backend setup

Needs Python 3.10+ (`uv` handles this).

```bash
cd backend
cp .env.example .env          # add HYDRA_DB_API_KEY + NEBIUS_API_KEY (both optional)
uv venv --python 3.12
uv pip install fastapi "uvicorn[standard]" openai anthropic python-dotenv hydra-db-python
uv run uvicorn app.main:app --reload --port 8000
```

**It runs with zero keys** in *offline mode* (memory mirrored locally, LLM faked
from a seed answer key) so Alex can build the frontend immediately. Add keys to
flip to real HydraDB + real inference — no code changes.

**LLM provider:** set `NEBIUS_API_KEY` to use Nebius Token Factory (free credits,
default), or `ANTHROPIC_API_KEY` for Claude. Auto-prefers Nebius if both are set;
force with `LLM_PROVIDER=nebius|anthropic|none`.

Check status anytime: `GET /` → `{"mode": "hydradb"|"offline", "llm": "nebius:meta-llama/..."|"anthropic"|"none"}`.

---

## API contract (for the frontend)

Base URL `http://localhost:8000`. CORS is open.

### `POST /ingest` — Session 1: agent reads convos, writes memory
```json
{ "mode": "hydradb", "claude": true,
  "coins_created": ["marc::ghosting","sarah::broken_promise","tom::transactional"],
  "count": 3 }
```

### `GET /dashboard` — the whole game world, derived from recall
```json
{ "mode": "hydradb",
  "goblin": { "stage": 2, "name": "Greedy Goblin", "bag_weight": 3 },
  "contacts": [
    { "name": "Marc", "relationship_type": "friend", "score": 66,
      "state": "neglected", "warning": "entering decay zone",
      "open_coin_count": 1, "main_pattern": "ghosting",
      "predicted": { "pattern": "ghosting", "color": "purple",
                     "reason": "...17 days old and unaddressed.", "repairable": true } },
    { "name": "Nina", "score": 100, "state": "healthy", "predicted": null, "...": "..." }
  ],
  "coins": [ { "source_id": "marc::ghosting", "contact": "Marc", "pattern": "ghosting",
               "color": "purple", "label": "Ghosting", "severity": "high",
               "age_days": 17, "status": "open", "summary": "...", "evidence": ["..."] } ],
  "trace_count": 12 }
```
`state` is one of: `healthy, hungry, neglected, angry, rotting, zombie`.
`goblin.stage` 1–4 → `Little Imp, Greedy Goblin, Pattern Hoarder, Dark Goblin`.
Coin colors: `purple` ghosting, `yellow` broken_promise, `red` bad_excuse, `blue` transactional.

### `GET /coin?id=marc::ghosting` — inspector (recall → personalized repair)
```json
{ "coin": { "...": "decorated coin" },
  "evidence": ["Marc sent the last message 17 days ago","..."],
  "retrieved_memory": ["Ghosting with Marc: 17 days...","Marc: friend. Prefers short honest..."],
  "prediction": "In a few more days this turns into an apology.",
  "smallest_action": "Send one honest acknowledgement, no excuse.",
  "suggested_message": "Hey Marc — I went quiet on this, sorry. Still up for it this week?",
  "why_personalized": "Based on remembered context: Marc responded well to short honesty" }
```
Show `retrieved_memory` in the UI — it's the visible proof that recall shaped the answer.

### `POST /repair` — complete a repair
Body: `{ "coin_id": "marc::ghosting" }`
```json
{ "resolved": "marc::ghosting",
  "goblin": { "stage": 1, "name": "Little Imp", "bag_weight": 2 },
  "contact": { "name": "Marc", "score": 100, "state": "healthy", "warning": "" } }
```

### `GET /trace` — the HydraDB memory log (proof panel)
```json
{ "mode": "hydradb",
  "lines": [ { "ts": "11:33:05", "op": "WRITE", "detail": "coin: marc::ghosting", "mode": "hydradb" },
             { "ts": "11:33:06", "op": "QUERY", "detail": "all open ... coins", "mode": "hydradb" } ] }
```
`op` ∈ `SETUP, WRITE, QUERY, ERROR`. Render WRITE green, QUERY blue.

### `POST /reset` — re-run the demo
- `POST /reset` (soft): wipe the local cache + trace, **leave HydraDB intact** — so the next load re-proves cross-session recall.
- `POST /reset?hard=true`: also delete all memories from HydraDB for a fully clean re-run (use before a fresh live-repair demo).

---

## Demo script (4 scenes)

1. **Session 1 — memory creation.** Hit `/ingest`. Trace panel fills with
   `[HydraDB WRITE]` lines. Coins drop, the Goblin collects them.
2. **Session 2 — recall.** Restart the backend (or `/reset`), load `/dashboard`.
   The world rebuilds from `[HydraDB QUERY]` — *nothing was stored locally*.
3. **Context-aware repair.** Click Marc's coin → `/coin`. The suggestion is
   personalized from recalled memory. Show the `retrieved_memory` list.
4. **Repair + evolve.** `/repair` Marc. Coin vanishes, Goblin shrinks, Marc heals.
   Reload `/dashboard` — Marc stays fixed. The agent learned.

Contacts in the seed: **Marc** (ghosting → live repair), **Sarah** (broken
promise → prediction), **Tom** (transactional → structural), **Nina** (healthy
control).
