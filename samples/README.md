# Sample chats for `/ingest_raw`

Two real-world-ish chat files to test ingesting actual conversations (not the seed).
They use people who aren't in the seed (Dev, Maya), so coins appearing for them proves
the ingestion is live.

## `whatsapp_dev.txt` — WhatsApp export format (deterministic parser)

A WhatsApp "export chat" `.txt`. Dev asks twice to meet, the user goes silent → **ghosting**.
Your own messages are labeled `Rohit`, so pass that as `your_name`.

```bash
curl -X POST localhost:8000/ingest_raw \
  -H 'content-type: application/json' \
  -d "{\"source\":\"whatsapp\",\"your_name\":\"Rohit\",\"text\":$(python3 -c 'import json,sys;print(json.dumps(open("samples/whatsapp_dev.txt").read()))')}"
```

## `imessage_maya.txt` — free-form paste (LLM normalizer)

A copied iMessage-style thread with no strict timestamps. The user keeps re-promising
coffee → **broken promise**. Use `source:"auto"` so the LLM normalizes it.

```bash
curl -X POST localhost:8000/ingest_raw \
  -H 'content-type: application/json' \
  -d "{\"source\":\"auto\",\"your_name\":\"Me\",\"text\":$(python3 -c 'import json,sys;print(json.dumps(open("samples/imessage_maya.txt").read()))')}"
```

Then `GET /dashboard` and you'll see Dev / Maya appear alongside the seed cast.

> Note: the WhatsApp dates are set near the hackathon window (June 2026) so the
> "days ago" ages read correctly on demo day. The deterministic parser computes
> ages from the real current date.
