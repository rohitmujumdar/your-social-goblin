"""Seeded demo data = the script of the demo.

Each contact has:
  - messages: the fake conversation (day = days before DEMO_NOW). Fed to Claude.
  - profile:  relationship memory (tone + repair strategy) written to HydraDB.
  - answer_key: the coins we KNOW are in this convo. Used as the safe fallback
                when Claude is off or returns garbage, so the demo never breaks.

Three arcs that each prove a different capability:
  Marc  -> ghosting, the live REPAIR demo
  Sarah -> broken promise, the PREDICTION demo (about to repeat)
  Tom   -> transactional, a structural pattern (not the user's fault)
  Nina  -> healthy control, proves it isn't just doom
"""

SEED = {
    "Marc": {
        "relationship_type": "friend",
        "profile": {
            "tone": "short, casual, honest",
            "repair_strategy": "a brief honest acknowledgement, never a long excuse",
            "note": "dislikes vague promises; responded well to short honesty before",
        },
        "messages": [
            {"day": 30, "sender": "user", "text": "we should finally grab that coffee soon"},
            {"day": 24, "sender": "Marc", "text": "yes definitely! when are you free?"},
            {"day": 17, "sender": "Marc", "text": "still up for it? this week works for me"},
            # Marc asked twice, user went silent -> unambiguous 17-day ghost
        ],
        "answer_key": [
            {
                "pattern": "ghosting",
                "severity": "high",
                "age_days": 17,
                "summary": "Ghosting with Marc: he asked twice to meet and you went silent for 17 days.",
                "evidence": [
                    "Marc sent the last two messages",
                    "You haven't replied in 17 days",
                    "An open coffee plan is left hanging",
                ],
            }
        ],
    },
    "Sarah": {
        "relationship_type": "colleague",
        "profile": {
            "tone": "practical, low-drama",
            "repair_strategy": "a concrete follow-up with a date beats an emotional apology",
            "note": "responds to action, not words",
        },
        "messages": [
            {"day": 12, "sender": "user", "text": "I'll send over the deck by Friday, promise"},
            {"day": 9, "sender": "Sarah", "text": "no rush! whenever you get a sec"},
            {"day": 3, "sender": "Sarah", "text": "hey any luck with that deck?"},
            {"day": 3, "sender": "user", "text": "yes almost done, sending tomorrow!"},
            # 'sending tomorrow' said 3 days ago, deck still not sent -> broken promise,
            # and the pattern is about to repeat -> prediction target
        ],
        "answer_key": [
            {
                "pattern": "broken_promise",
                "severity": "medium",
                "age_days": 12,
                "summary": "Broken promise with Sarah: deck promised 12 days ago, re-promised 'tomorrow' 3 days ago, still not sent.",
                "evidence": [
                    "Promised the deck 'by Friday' 12 days ago",
                    "Re-promised 'tomorrow' 3 days ago",
                    "Deck still not delivered",
                ],
            }
        ],
    },
    "Tom": {
        "relationship_type": "weak tie",
        "profile": {
            "tone": "friendly but balanced",
            "repair_strategy": "a no-ask message that gives instead of requests",
            "note": "almost every exchange is you needing something",
        },
        "messages": [
            {"day": 40, "sender": "user", "text": "hey Tom! could you intro me to your designer?"},
            {"day": 39, "sender": "Tom", "text": "sure, done"},
            {"day": 14, "sender": "user", "text": "Tom quick one, can you review my portfolio?"},
            {"day": 13, "sender": "Tom", "text": "ok sent some notes"},
            {"day": 2, "sender": "user", "text": "hey can you forward me that contact again?"},
        ],
        "answer_key": [
            {
                "pattern": "transactional",
                "severity": "medium",
                "age_days": 40,
                "summary": "Transactional pattern with Tom: 3 of your last 3 messages were asks, no give-back.",
                "evidence": [
                    "Every recent message from you is a request",
                    "No reciprocal or no-ask outreach",
                    "Relationship is becoming extractive",
                ],
            }
        ],
    },
    "Nina": {
        "relationship_type": "close friend",
        "profile": {
            "tone": "warm, frequent",
            "repair_strategy": "nothing to repair, keep it up",
            "note": "healthy loop, balanced give and take",
        },
        "messages": [
            {"day": 5, "sender": "Nina", "text": "loved that book you sent!"},
            {"day": 5, "sender": "user", "text": "right?? lunch sunday to discuss?"},
            {"day": 4, "sender": "Nina", "text": "yes! see you then"},
            {"day": 1, "sender": "user", "text": "that was so fun, miss you already"},
        ],
        "answer_key": [],  # healthy: no coins
    },
}


def contact_names():
    return list(SEED.keys())
