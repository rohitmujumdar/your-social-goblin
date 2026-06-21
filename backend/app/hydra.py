"""HydraDB wrapper. ALL HydraDB access goes through here, for two reasons:

1. Every call appends a line to TRACE -> that's the "execution logs" deliverable
   the judges require, and the terminal panel Alex renders.
2. One place to fix if the SDK method signatures differ from what we coded.

Design note on the MIRROR:
   We keep an in-process dict of coins keyed by source_id. It is a CACHE, not the
   source of truth. HydraDB is the source of truth. Why keep a mirror?
     - HydraDB indexing can lag a beat after a write; the mirror keeps the demo
       consistent within a session.
     - On a COLD START (new process = "new session"), the mirror is EMPTY, so the
       dashboard MUST rebuild from a real HydraDB recall. That is exactly the
       cross-session persistence proof.
"""
import datetime
import json

from . import config

try:
    from hydra_db import HydraDB  # type: ignore
    _SDK_OK = True
except Exception:  # SDK not installed yet -> offline mode still works
    HydraDB = None
    _SDK_OK = False


TRACE = []                 # list[{"ts","op","detail","mode"}]
MIRROR = {}                # source_id -> coin dict (cache)
PROFILES = {}              # contact -> profile text (cache)


def _now_iso():
    return datetime.datetime.now().strftime("%H:%M:%S")


def log(op, detail, mode):
    TRACE.append({"ts": _now_iso(), "op": op, "detail": detail, "mode": mode})
    # keep the panel readable
    if len(TRACE) > 200:
        del TRACE[:-200]


class Hydra:
    def __init__(self):
        self.online = bool(config.HYDRA_DB_API_KEY) and _SDK_OK
        self.client = None
        if self.online:
            try:
                self.client = HydraDB(token=config.HYDRA_DB_API_KEY)
            except Exception as e:
                log("ERROR", f"HydraDB init failed: {e}; falling back to offline", "offline")
                self.online = False

    @property
    def mode(self):
        return "hydradb" if self.online else "offline"

    def ensure_tenant(self):
        if not self.online:
            log("SETUP", "offline mode (no HYDRA_DB_API_KEY) — memory mirrored locally", "offline")
            return
        try:
            self.client.tenant.create(tenant_id=config.TENANT_ID)
        except Exception:
            pass  # already exists is fine
        log("SETUP", f"tenant '{config.TENANT_ID}' ready", "hydradb")

    # ---- WRITES ----
    def write_memory(self, text, source_id, metadata):
        """Write one memory. Updates the mirror, then HydraDB (if online)."""
        kind = metadata.get("kind")
        if kind == "coin":
            MIRROR[source_id] = {**metadata, "source_id": source_id, "text": text}
        elif kind == "repair":
            target = metadata.get("resolves")
            if target and target in MIRROR:
                MIRROR[target]["status"] = "resolved"
        elif kind == "profile":
            PROFILES[metadata.get("contact")] = text

        if self.online:
            try:
                # HydraDB wants document_metadata as a JSON STRING, and it drops
                # numeric values (keeps strings + lists), so stringify scalars.
                hydra_meta = {k: (v if isinstance(v, (str, list)) else
                                  ("" if v is None else str(v)))
                              for k, v in metadata.items()}
                self.client.upload.add_memory(
                    tenant_id=config.TENANT_ID,
                    sub_tenant_id=config.USER_ID,
                    upsert=True,
                    memories=[{
                        "text": text,
                        "source_id": source_id,
                        "infer": False,
                        "document_metadata": json.dumps(hydra_meta),
                    }],
                )
            except Exception as e:
                log("ERROR", f"write failed ({source_id}): {e}", "offline")
        log("WRITE", f"{kind}: {source_id}", self.mode)

    # ---- READS ----
    def recall(self, query, max_results=30):
        """Hybrid recall from HydraDB. Logs the query, hydrates the mirror, and
        ALWAYS returns from the mirror so derivation is consistent even if indexing
        lags. The real query still happens and still appears in the trace."""
        if self.online:
            try:
                # recall_preferences searches MEMORIES (full_recall searches knowledge
                # sources, which we don't use). Returns instantly, no indexing lag.
                res = self.client.recall.recall_preferences(
                    tenant_id=config.TENANT_ID,
                    sub_tenant_id=config.USER_ID,
                    query=query,
                    max_results=max_results,
                )
                resolved = set()
                for m in _normalize_recall(res):
                    md = m.get("metadata") or {}
                    sid = m.get("source_id") or md.get("source_id")
                    if md.get("kind") == "coin" and sid:
                        md["age_days"] = int(md.get("age_days") or 0)  # un-stringify
                        # hydrate cache from HydraDB (this is the cross-session rebuild)
                        MIRROR.setdefault(sid, {**md, "source_id": sid, "text": m.get("text", "")})
                    elif md.get("kind") == "profile" and md.get("contact"):
                        PROFILES.setdefault(md["contact"], m.get("text", ""))
                    elif md.get("kind") == "repair":
                        # the repair memory marks its coin resolved across sessions
                        tgt = md.get("resolves")
                        if not tgt and sid and sid.endswith("::repair"):
                            tgt = sid[: -len("::repair")]
                        if tgt:
                            resolved.add(tgt)
                for tgt in resolved:
                    if tgt in MIRROR:
                        MIRROR[tgt]["status"] = "resolved"
            except Exception as e:
                log("ERROR", f"recall failed: {e}", "offline")
        log("QUERY", query, self.mode)
        return list(MIRROR.values())

    def recall_text(self, query, max_results=10):
        """Like recall but returns raw text snippets for feeding to Claude."""
        coins = self.recall(query, max_results)
        snippets = [c.get("text", "") for c in coins]
        snippets += [v for v in PROFILES.values()]
        return [s for s in snippets if s]

    def list_memory_ids(self):
        if not self.online:
            return []
        try:
            r = self.client.fetch.list_data(tenant_id=config.TENANT_ID,
                                             sub_tenant_id=config.USER_ID, kind="memories")
            d = r.model_dump() if hasattr(r, "model_dump") else r
            return [m["memory_id"] for m in (d.get("user_memories") or [])]
        except Exception as e:
            log("ERROR", f"list failed: {e}", "offline")
            return []

    def purge(self):
        """Delete ALL of this user's memories from HydraDB + clear the cache.
        Lets you re-run the full demo (incl. the live repair) from scratch."""
        MIRROR.clear()
        PROFILES.clear()
        n = 0
        for mid in self.list_memory_ids():
            try:
                self.client.upload.delete_memory(tenant_id=config.TENANT_ID,
                                                  sub_tenant_id=config.USER_ID, memory_id=mid)
                n += 1
            except Exception as e:
                log("ERROR", f"delete {mid}: {e}", "offline")
        log("SETUP", f"purged {n} memories from HydraDB", self.mode)
        return n


def _as_dict(obj):
    """document_metadata may come back as a pydantic model or a dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    for attr in ("model_dump", "dict"):
        if hasattr(obj, attr):
            try:
                return getattr(obj, attr)()
            except Exception:
                pass
    return {}


def _normalize_recall(res):
    """full_recall returns a RetrievalResult with .chunks (list of VectorStoreChunk).
    Pull each chunk into {text, metadata, source_id}, reviving the JSON payload."""
    chunks = getattr(res, "chunks", None)
    if chunks is None and isinstance(res, dict):
        chunks = res.get("chunks")
    def g(ch, attr):
        return getattr(ch, attr, None) if not isinstance(ch, dict) else ch.get(attr)

    out = []
    for ch in chunks or []:
        # HydraDB returns our parsed metadata in additional_metadata (a dict);
        # fall back to a JSON-string document_metadata if that's ever populated.
        md = _as_dict(g(ch, "additional_metadata"))
        if not md:
            raw = g(ch, "document_metadata")
            if isinstance(raw, str):
                try:
                    md = json.loads(raw)
                except Exception:
                    md = {}
            else:
                md = _as_dict(raw)
        text = g(ch, "chunk_content") or ""
        sid = g(ch, "source_id")
        out.append({"text": text, "metadata": md, "source_id": sid})
    return out


# single shared instance
db = Hydra()
