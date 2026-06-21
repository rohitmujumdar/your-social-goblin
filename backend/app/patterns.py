"""Pure functions that DERIVE the game state from coins. No state stored here.

This is the heart of "derive, don't store": Tamagotchi health, the Goblin's
size, and warnings are all computed fresh from the list of open coins every time.
Deterministic on purpose so the demo is fast and repeatable (no LLM in this path).
"""
from .config import SEVERITY_WEIGHT, PATTERN_COLORS, PATTERN_LABELS


def tamagotchi_state(open_coins, days_since_last_positive=0):
    """Map a contact's open coins -> (score 0..100, visual state, warning text)."""
    penalty = sum(SEVERITY_WEIGHT.get(c.get("severity", "medium"), 22) for c in open_coins)
    penalty += min(days_since_last_positive, 30) // 3  # slow drift from silence
    score = max(0, 100 - penalty)

    if score >= 85:
        state = "healthy"
    elif score >= 68:
        state = "hungry"
    elif score >= 45:
        state = "neglected"
    elif score >= 25:
        state = "angry"
    elif score >= 10:
        state = "rotting"
    else:
        state = "zombie"

    warning = ""
    if state in ("neglected", "angry"):
        warning = "entering decay zone"
    elif state in ("rotting", "zombie"):
        warning = "critical, repair now"
    elif open_coins:
        warning = "watch this one"

    return score, state, warning


def goblin_stage(total_open_coins):
    """Total open coins across all contacts -> the Goblin's evolution stage."""
    n = total_open_coins
    if n <= 2:
        stage, name = 1, "Little Imp"
    elif n <= 6:
        stage, name = 2, "Greedy Goblin"
    elif n <= 11:
        stage, name = 3, "Pattern Hoarder"
    else:
        stage, name = 4, "Dark Goblin"
    return {"stage": stage, "name": name, "bag_weight": n}


def decorate_coin(coin):
    """Attach display fields (color, label) a coin needs in the UI."""
    pattern = coin.get("pattern", "ghosting")
    coin["color"] = PATTERN_COLORS.get(pattern, "gray")
    coin["label"] = PATTERN_LABELS.get(pattern, pattern.title())
    return coin
