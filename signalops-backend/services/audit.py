"""Append-only audit log (JSONL). Survives backend restarts; investigations themselves are in memory."""
import json
import os
import pathlib
import uuid
from datetime import datetime, timezone

PATH = pathlib.Path(os.getenv("AUDIT_LOG", pathlib.Path(__file__).resolve().parent.parent / "audit.jsonl"))


def record(event: str, **fields) -> dict:
    entry = {"audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
             "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **fields}
    with PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def entries(investigation_id: str | None = None) -> list[dict]:
    if not PATH.exists():
        return []
    rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if investigation_id in (None, r.get("investigation_id"))][::-1]  # newest first
