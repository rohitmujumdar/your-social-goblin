"""Source adapters: turn a raw chat export into our normalized shape
    {contact, messages:[{sender:'user'|<contact>, day:<days ago>, text}]}
so the SAME detect -> store pipeline runs on real chats, not just seed data.

Two ways in:
  - parse_whatsapp(): deterministic parser for WhatsApp "export chat" .txt files.
  - (LLM fallback lives in agent.normalize_chat() — handles any pasted format.)
"""
import datetime
import re

# WhatsApp lines look like either:
#   [2026-06-04, 2:21:13 PM] Marc: still up for coffee?      (iOS)
#   6/4/26, 14:21 - Marc: still up for coffee?               (Android)
_IOS = re.compile(r"^\[(?P<dt>[^\]]+)\]\s*(?P<sender>[^:]+?):\s*(?P<text>.*)$")
_ANDROID = re.compile(
    r"^(?P<dt>\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:[APap][Mm])?)\s*-\s*"
    r"(?P<sender>[^:]+?):\s*(?P<text>.*)$"
)
_DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%y", "%m/%d/%Y", "%d/%m/%y", "%d/%m/%Y", "%d.%m.%Y",
]


def _parse_day(dt_str, today):
    """Best-effort: turn a WhatsApp date string into 'days ago'. None if unparseable."""
    date_part = dt_str.split(",")[0].strip()
    for fmt in _DATE_FORMATS:
        try:
            d = datetime.datetime.strptime(date_part, fmt).date()
            return max(0, (today - d).days)
        except ValueError:
            continue
    return None


def parse_whatsapp(text, you_names=("me", "you")):
    """Parse a WhatsApp export. Returns (contact, messages) or None if it doesn't look
    like WhatsApp. 'you_names' are the labels that map to sender 'user'."""
    today = datetime.date.today()
    you = {n.strip().lower() for n in you_names if n}
    rows = []
    for line in text.splitlines():
        m = _IOS.match(line.strip()) or _ANDROID.match(line.strip())
        if not m:
            continue
        rows.append((m.group("sender").strip(), m.group("text").strip(),
                     _parse_day(m.group("dt"), today)))
    if len(rows) < 2:
        return None  # not WhatsApp (or empty) -> let the LLM normalizer try

    # the contact = the most common sender who isn't you
    others = [s for s, _, _ in rows if s.lower() not in you]
    if not others:
        return None
    contact = max(set(others), key=others.count)

    # fill missing days by even spacing (newest last) so aging still works
    n = len(rows)
    messages = []
    for i, (sender, body, day) in enumerate(rows):
        if day is None:
            day = (n - 1 - i) * 2  # crude fallback ordering
        messages.append({
            "sender": "user" if sender.lower() in you else contact,
            "day": day, "text": body,
        })
    return contact, messages
