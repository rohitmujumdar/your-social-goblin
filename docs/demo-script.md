# Your Social Goblin — Demo Script (~2:45)

**0:00 — Hook**
*(facing the audience, screen not shared yet / on the cover slide)*

> "Raise your hand if there's someone you've been meaning to text back for two weeks.
> *(beat)* Yeah — me too. Most AI agents have that exact problem: close the tab, and
> they forget you. We built the opposite."

**0:18 — What it is**
*(share screen → dashboard)*

> "This is Your Social Goblin. Every relationship is a little creature, and its health
> is the health of that relationship. Treat someone badly — ghost them, break a promise
> — and a coin drops. This goblin hoards every coin you refuse to repair. And every coin
> is a memory, stored in HydraDB."

**0:40 — Scene 1: the world**
*(point at the creatures)*

> "It read these chats and drew this. Marc — health 66, I went silent on him for 17 days:
> purple coin, ghosting. Sarah — I promised her a deck and never sent it: yellow coin.
> Tom — every message I send him is an ask: blue coin. And Nina — green, healthy, no coin.
> It knows when I'm actually doing fine."

**1:05 — Scenes 2/3: context-aware**
*(click Marc's coin, then Sarah's)*

> "Click Marc's coin. The agent doesn't just flag it — it pulls what it remembers about
> Marc: short, casual, honest, hates long excuses. So it drafts this message, in his tone.
> *(click Sarah)* Sarah's different — she responds to action, not words — so it pushes a
> concrete date instead. Same agent, different memory, different advice."

**1:35 — Scene 4: repair + evolve**
*(click "repair" on Marc)*

> "I fix Marc. *(click)* Coin gone, goblin shrinks, Marc heals back to 100 — and underneath,
> the agent writes a new memory: Marc, resolved."

**1:55 — Scene 5: THE MEMORY MOMENT (the climax)**
*(soft reset / reload — see prep below)*

> "Now the real test. I close it — *(reload)* — the app remembers nothing in its own head.
> It boots blank and asks HydraDB: what do you remember about me? *(the world rebuilds)*
> Sarah and Tom still have their coins. But Marc? Still healed — it won't re-flag him,
> because it remembers I fixed him. *(point at the trace panel)* And every read and write
> you're seeing is live, in the memory log."

**2:35 — Close**
*(facing the audience)*

> "Most agents forget you the second you leave. This one remembers the relationships you're
> letting rot, predicts the next one you'll drop, and gets smarter every time you show up.
> The goblin only feeds on what you refuse to repair — your job is to stop feeding him.
> *(beat)* That's Your Social Goblin."

---

## Demo prep checklist

- [ ] Backend up with **both** keys set (`HYDRA_DB_API_KEY`, `NEBIUS_API_KEY`); `GET /` shows `"mode":"hydradb"`.
- [ ] Clean slate before you start: `POST /reset?hard=true` then `POST /ingest` → 3 coins (Marc/Sarah/Tom open, Nina healthy).
- [ ] **Scene 5 is the climax — rehearse the exact sequence.** A plain browser reload is NOT enough to prove persistence (the backend cache can still be warm). To genuinely rebuild from HydraDB, do ONE of these right before the reload:
  - restart the backend, **or**
  - call `POST /reset` (soft — clears the in-process cache, keeps HydraDB), then reload the page.
  The dashboard then rebuilds entirely from a HydraDB recall, with Marc still resolved.
- [ ] Have the **trace panel** visible so the live `WRITE` / `QUERY` lines are on screen during Scene 5.
- [ ] Accuracy note: the live cast is the **seeded** Marc/Sarah/Tom/Nina. If you want "real chats" to be literally true, ingest a sample (`samples/whatsapp_dev.txt`) beforehand; otherwise say "these chats," not "my real chats."
