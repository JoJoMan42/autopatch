from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from patchpilot.db.models.audit import AuditEventModel


def compute_audit_hash(
    prev_hash: str | None,
    ts: datetime,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content = f"{prev_hash or '0'*64}:{ts.isoformat()}:{actor}:{action}:{entity_type}:{entity_id}:{canonical_payload}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def record_audit_event(
    db: Session,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
) -> AuditEventModel:
    """Append a hash-chained audit record in the current transaction."""
    # Fetch the latest audit event to get prev_hash
    stmt = select(AuditEventModel).order_by(AuditEventModel.ts.desc()).limit(1)
    last_event = db.scalar(stmt)
    prev_hash = last_event.hash if last_event else "0" * 64

    ts = datetime.now(timezone.utc)
    event_hash = compute_audit_hash(
        prev_hash=prev_hash,
        ts=ts,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
    )

    audit_event = AuditEventModel(
        ts=ts,
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
        prev_hash=prev_hash,
        hash=event_hash,
    )
    db.add(audit_event)
    return audit_event

