"""Minimal decision events (MVP-FR-029, THIN). No PII in metadata."""
from typing import Optional

from sqlalchemy.orm import Session

from db.models import DecisionEvent


def event(db: Session, event_type: str, session_id=None, line_id=None, actor_id: Optional[str] = None,
          suggested_sku=None, selected_sku=None, match_score=None, reason_code=None, **metadata) -> None:
    db.add(DecisionEvent(session_id=session_id, line_id=line_id, event_type=event_type, actor_id=actor_id,
                         suggested_sku=suggested_sku, selected_sku=selected_sku, match_score=match_score,
                         reason_code=reason_code, metadata_=metadata))
