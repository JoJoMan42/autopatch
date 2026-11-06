from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from patchpilot.db.models.job import JobEventModel


def publish_job_event(
    db: Session,
    job_id: str,
    event_type: str,
    data: dict[str, Any],
) -> JobEventModel:
    """Persist ordered job event to database and optionally publish to Redis."""
    # 1. Determine next sequence number
    stmt = (
        select(func.coalesce(func.max(JobEventModel.seq), 0))
        .where(JobEventModel.job_id == job_id)
    )
    last_seq = db.scalar(stmt) or 0
    next_seq = last_seq + 1

    ts = datetime.now(timezone.utc)
    event_record = JobEventModel(
        job_id=job_id,
        seq=next_seq,
        type=event_type,
        data=data,
        created_at=ts,
    )
    db.add(event_record)

    # 2. Publish to Redis channel if redis is available
    try:
        import redis
        from patchpilot.config import get_settings

        r = redis.Redis.from_url(get_settings().redis_url, socket_timeout=1.0)
        channel = f"job:{job_id}"
        message_payload = json.dumps(
            {
                "v": 1,
                "seq": next_seq,
                "type": event_type,
                "job_id": job_id,
                "ts": ts.isoformat(),
                "data": data,
            }
        )
        r.publish(channel, message_payload)
    except Exception:
        # Don't let transient redis failure break core DB transaction
        pass

    return event_record

