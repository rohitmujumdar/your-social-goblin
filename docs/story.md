# Your Social Goblin — Visual Story

A scene-by-scene script for the presentation. Each scene has a one-line beat and a
ready-to-paste **image prompt**. Prepend the **style block** to every prompt so all
the generated images look like one coherent set.

> **This whole story is really about one thing: memory.** The two judging criteria
> run through the scenes:
> - **Persistent memory (autonomous recall across sessions)** — Scenes 1 & 5: the
>   world is written to HydraDB, then a *fresh* session rebuilds it entirely from
>   recall. Fixed things stay fixed.
> - **Context-aware execution (memory changes the action)** — Scenes 3 & 5b: the
>   repair it suggests depends on *who* it remembers the person being and *what
>   worked before*. Same app, different advice per person and per history.

---

## 🎨 Style block (prepend to every prompt)

> Cozy hand-drawn game-UI illustration, soft rounded shapes, warm dark-violet
> background (#0c0a12) with gold coin accents. Cute Tamagotchi-style creatures and
> a small mischievous goblin. Flat, modern, friendly, slightly storybook. Limited
> palette: deep purple, charcoal, gold, with four coin colors — purple, yellow, red,
> blue. Clean, no clutter, no text in the image unless asked.

Coin colors (keep consistent everywhere):
- 🟣 **purple** = ghosting
- 🟡 **yellow** = broken promise
- 🔴 **red** = bad excuse
- 🔵 **blue** = transactional

---

## Cover

**Beat:** The world in one frame — your relationships as living creatures, a goblin
hoarding the parts you won't repair.

**Image prompt:** A cozy dashboard world at night. Four cute Tamagotchi creatures of
different moods scattered on soft floating platforms; a small round goblin in the
center carrying a bulging bag of glowing colored coins, grinning. Title space at top.
Warm gold light, deep violet backdrop.

---

## Character sheet

**Beat:** Meet the cast. Each creature's look = the health of that relationship.

**Image prompt:** A character lineup of four cute creatures, left to right:
1) **Marc** — grey, droopy, sleepy-sad ("neglected"), a purple coin near him.
2) **Sarah** — tired but okay ("hungry"), a yellow coin near her.
3) **Tom** — wary, arms-crossed ("hungry"), a blue coin near him.
4) **Nina** — bright, bouncy, glowing healthy, no coin.
Simple flat style, soft outlines, consistent proportions, on a dark violet strip.

**Goblin evolution prompt:** The same little goblin shown in four growth stages
left to right, getting bigger, darker, and more overloaded with a heavier coin bag:
"Little Imp" → "Greedy Goblin" → "Pattern Hoarder" → "Dark Goblin". Cute-to-menacing
gradient, playful.

---

## Scene 1 — You open the app

**Beat:** The app reads your chats and draws the world. Coins drop from the people
you've been treating badly; Nina stays bright.

**Image prompt:** A game dashboard waking up. Three creatures (grey Marc, tired Sarah,
wary Tom) each dropping a colored coin (purple, yellow, blue), while a fourth (Nina)
glows happily with no coin. A small goblin trots in from the side, eyeing the coins.

---

## Scene 2 — You open the Goblin's bag

**Beat:** The bag is a window into memory — every coin is something you're avoiding.

**Image prompt:** Close-up of the goblin opening a worn leather bag that spills a few
glowing coins, each labeled by color (purple, yellow, blue). The open bag glows softly
from within, like a little inventory screen. Warm, inviting, slightly magical.

---

## Scene 3 — You click Marc's coin

**Beat:** The app explains the habit and writes a fix in *Marc's* tone, using what it
remembers about him.

**Image prompt:** An inspector card floating beside grey droopy Marc, showing a purple
coin, a tiny "17 days" hourglass, and a glowing speech bubble with a short friendly
message forming. The card feels like a gentle coaching tooltip, not a scold.

**✓ Proves — context-aware execution:** the message is short and honest *because*
memory says Marc dislikes long excuses. For Sarah, the same app suggests a concrete
date instead. The recommendation is shaped by recalled history, not a fixed template.

---

## Scene 4 — You fix it

**Beat:** Coin gone, Marc heals, the goblin shrinks. The app records that you fixed it.

**Image prompt:** A before/after split. Left: grey sad Marc with a purple coin and a
chubby goblin. Right: bright happy healed Marc, the coin dissolving into sparkles, and
the goblin noticeably smaller and grumpier. Satisfying, warm, rewarding.

---

## Scene 5 — You close it and come back (the memory moment)

**Beat:** The app reopens blank and rebuilds the whole world from memory. Fixed things
stay fixed; unfixed things still rot.

**Image prompt:** A dark screen powering back on, and the creature world reassembling
itself from glowing coins flowing out of a central "notebook/database" crystal. Marc is
still healthy; Sarah and Tom still have their coins. A sense of memory restoring a world.

**✓ Proves — persistent memory:** nothing was saved as app state; the entire world is
recalled from HydraDB on load. Marc stays fixed because his resolution memory persists
across the session boundary.

---

## Scene 5b — It remembers what worked (the learned loop)

**Beat:** Weeks later Marc slips again. Before advising, the app recalls "short honesty
worked with Marc last time" and leans on it — citing the past outcome, not a guess.

**Image prompt:** Grey Marc again with a faint purple coin, and a glowing thread linking
him back to a small lit-up "memory" icon. A speech bubble forms that references the past
("last time, keeping it short worked"). The feeling: the app learning from its own history.

**✓ Proves — context-aware execution across sessions:** the recommendation is shaped by
a stored *outcome* from a previous session, recalled autonomously. This is the live
`learned_from_past` field in the `/coin` response.

---

## Scene 6 — The prediction (Sarah)

**Beat:** It warns you before a habit repeats — a coin glows above Sarah before it drops.

**Image prompt:** Tired Sarah with a yellow coin hovering and pulsing above her head,
not yet dropped, a faint warning aura around her. The goblin leans toward her, drooling
hopefully, anticipating the coin. Tense but cute.

---

## Scene 7 — The proof panel

**Beat:** A live log shows every real read/write to memory — proof it's not faked.

**Image prompt:** A small retro terminal panel glowing in the corner of the dashboard,
scrolling lines of gold and teal text (writes and reads) next to the goblin world.
Hacker-cozy, CRT glow, but clean and readable.

---

> The Goblin feeds on the parts of your relationships you refuse to repair.
> Your job isn't to kill him — it's to understand what he's eating, and stop feeding him.

