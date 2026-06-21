# Your Social Goblin 🪙👹

A relationship-maintenance mini-game. Each contact is a Tamagotchi whose health
reflects the relationship. Detected "dark patterns" (ghosting, broken promises,
bad excuses, transactional behavior) become colored **coins** that a **Goblin**
collects. The Goblin grows heavier as your unresolved patterns pile up. Fix a
relationship and the coin vanishes, the Goblin shrinks, the Tamagotchi heals.

Built for the **"Agents you Love" hackathon** (theme: *Context over Amnesia*).
**HydraDB** is the memory brain; an LLM does the pattern-detection + repair logic.
The LLM provider is pluggable and defaults to **Nebius Token Factory** (free
credits, OpenAI-compatible); Anthropic Claude is the drop-in alternative.

📄 **More docs:** [`docs/architecture.html`](docs/architecture.html) (visual backend
walkthrough — open in a browser) · [`docs/story.md`](docs/story.md) (scene-by-scene
story + image prompts for slides).

## The pitch in one line

> The Goblin feeds on the parts of your relationships you refuse to repair.
> Every coin is a memory in HydraDB; close the tab and reopen — it remembers,
> predicts your next pattern, and adapts after you repair one.

---

## How the game works (a walkthrough)

You have relationships. Some you keep up with, some you let rot. The game turns
that invisible thing into a small world with three kinds of objects:

- **Tamagotchis** = your people. Each contact is a creature whose health = the
  health of that relationship.
- **Coins** = your bad habits. Treat someone badly (ghost them, break a promise)
  and a colored coin pops out of that person.
- **The Goblin** = the weight of everything you haven't fixed. He scoops the
  coins into his bag and grows fatter and darker the more you avoid.

The hook: you're not fighting the Goblin. He eats whatever you refuse to repair.
Your job is to stop feeding him.

### Scene 1 — You open the app

The app reads your recent conversations, studies each one ("is this person being
treated well or badly?"), and draws the world:

- **Marc** looks *neglected* (health **66**). You said "we should grab coffee," he
  replied twice asking when, and you went silent for **17 days**. A **purple coin**
  (purple = ghosting) dropped from him.
- **Sarah** looks *hungry* (**78**). You promised her a deck "by Friday," later said
  "sending tomorrow," and never delivered — a **yellow coin** (broken promise).
- **Tom** also *hungry* (**78**), but his issue is different: every message you send
  him is an ask. A **blue coin** (transactional).
- **Nina** is bright and *healthy* (**100**). Your chat is balanced and you both
  follow through. No coin — proof the app can tell when you're doing fine.

Off to the side, the **Goblin** holds **3 coins** (Marc, Sarah, Tom — not Nina),
which puts him at stage 2, the **"Greedy Goblin."** Let coins pile to 7+ and he
becomes a "Pattern Hoarder," past 12 a "Dark Goblin."

### Scene 2 — You click the Goblin's bag

His bag opens to a list of everything you're avoiding:

```
🟣 Ghosting        — Marc
🟡 Broken Promise  — Sarah
🔵 Transactional   — Tom
```

This list isn't hardcoded. Opening the bag asks HydraDB "what unresolved stuff do
you remember for this user?" and shows the notes that come back. The bag is a
window into the agent's memory.

### Scene 3 — You click Marc's purple coin

```
🟣 Ghosting — Marc

What happened:
You went silent on Marc for 17 days after he asked twice to meet.

Evidence:
• Marc sent the last two messages
• No reply from you in 17 days

Prediction:
Still fixable today. Wait longer and a casual reply becomes an awkward apology.

Smallest useful action:
Send one honest line. No long excuse.

Suggested message:
"Hey Marc, sorry I've been MIA, been busy but that's no excuse for not
responding. Will catch up soon."
```

The suggested message is **personalized from memory**: before writing it, the app
pulls its note on who Marc is ("prefers short, casual, honest; responds badly to
long excuses"). For Sarah, who "responds to action not words," the same app would
instead push you to give a concrete delivery date. Same app, different advice,
because it remembers different people differently.

### Scene 4 — You fix it

You send the message (or mark it done). Instantly: Marc's coin disappears from the
bag, the Goblin shrinks from "Greedy Goblin" (3 coins) to "Little Imp" (2 left),
and Marc heals from 66 back to 100. Underneath, the app writes a new memory: "user
repaired the Marc ghosting — resolved."

### Scene 5 — You close the app and come back

Reopen later (or restart the server) and the app starts blank — it remembers
nothing in its own head. So it asks HydraDB "what do you remember about this
user?" and rebuilds the world from the notes that return:

- Sarah and Tom still hungry with their coins (never fixed).
- Marc still healthy — his repair note is in memory, so the app won't re-flag him.
- Nina still glowing.

Nothing was saved as a score or screenshot. It is rebuilt from memory every time.

### Scene 6 — The prediction twist (Sarah)

The app also warns before a habit repeats:

```
⚠️ You're likely to break your promise to Sarah again.
Reason: a deck you promised is still open and aging, and you've re-promised once.
```

Visually that's a coin glowing above Sarah before it fully drops, and the Goblin
drifting toward her.

### Scene 7 — The proof panel

A terminal log scrolls every real read/write to HydraDB as it happens:

```
WRITE  coin: marc::ghosting
WRITE  coin: sarah::broken_promise
QUERY  open relationship dark patterns for the user
WRITE  repair: marc::ghosting::repair
QUERY  history and tone for Marc
```

### The whole game in five sentences

1. The app reads your conversations and turns each bad habit into a **coin** (a memory in HydraDB).
2. Your **people** look healthy or sick by how many coins they have, and the **Goblin** grows with the total you've left unfixed.
3. Click a coin and it explains the habit and suggests a fix **personalized to that person**, using what it remembers about them.
4. **Fix it** and the coin vanishes, the person heals, the Goblin shrinks, and the app records the fix.
5. **Come back later** and the world rebuilds from memory — fixed things stay fixed, unfixed things still rot, and it can **predict** the next slip before it happens.

> Scope note: the backend produces the health scores, coins, personalized
> suggestions, predictions, and the memory that survives restarts. The animations
> (the Goblin walking, coins dropping) are the frontend painting on top of that data.

---

## How memory works 

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

### `POST /ingest` — Session 1: agent reads the SEEDED convos, writes memory
```json
{ "mode": "hydradb", "claude": true,
  "coins_created": ["marc::ghosting","sarah::broken_promise","tom::transactional"],
  "count": 3 }
```

### `POST /ingest_raw` — ingest a REAL chat (WhatsApp export or pasted log)
Body: `{ "text": "<raw chat>", "your_name": "me", "source": "auto" }`
(`source`: `"whatsapp"` uses a fast deterministic parser; `"auto"` lets the LLM
normalize any format). It normalizes to the same shape as the seed, then runs the
identical detect → store pipeline.
```json
{ "mode": "hydradb", "contact": "Priya", "messages_parsed": 4,
  "coins_created": ["priya::broken_promise"], "count": 1 }
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
  "learned_from_past": ["a brief honest acknowledgement works with Marc"],
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
