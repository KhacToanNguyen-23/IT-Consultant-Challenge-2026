"""MVP-FR-021 (THIN): store-scoped "customer phrase -> SKU" memory.

* Recorded only AFTER Confirm, and only for lines where the associate chose the SKU themselves (SKU_EDITED event).
  Substituted lines are never recorded: the customer asked for a different product.
* Used as a small score boost (<= 0.20) on candidates the matcher already retrieved. It can never revive a candidate that
  failed a must-match rule and never lifts a line over a missing attribute: the hard rules run first.
* A removed (inactive) mapping is respected: it is not silently re-created by the next confirmation.
"""
import re
import unicodedata
from typing import Optional

from sqlalchemy.orm import Session

from db.models import DecisionEvent, OrderSession, SessionLine, StoreDictionary

DEFAULT_BOOST = 0.05
MAX_BOOST = 0.20


def normalize_phrase(text: Optional[str]) -> str:
    """Lower-case, punctuation to spaces, single spaces: 'Reglar 45x95, C24' == 'reglar 45x95 c24'."""
    t = unicodedata.normalize("NFKC", text or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]+", " ", t)).strip()


def record_after_confirm(db: Session, s: OrderSession, lines: list[SessionLine]) -> int:
    """Remember the SKUs the associate picked by hand. Returns how many new mappings were added."""
    chosen: dict = {}
    for e in db.query(DecisionEvent).filter(DecisionEvent.session_id == s.session_id, DecisionEvent.event_type == "SKU_EDITED") \
            .order_by(DecisionEvent.event_id):
        chosen[e.line_id] = e.selected_sku  # the last manual choice for a line wins
    added = 0
    for l in lines:
        sku = chosen.get(l.line_id)
        if not sku or l.final_sku != sku or l.fulfillment_action == "substituted":
            continue
        phrase = normalize_phrase(l.parsed_name)
        if not phrase:
            continue
        exists = db.query(StoreDictionary).filter_by(store_id=s.store_id, normalized_phrase=phrase, mapped_sku=sku).first()
        if exists:  # already known, or removed on purpose (inactive): leave it as it is
            continue
        db.add(StoreDictionary(store_id=s.store_id, normalized_phrase=phrase, mapped_sku=sku, boost=DEFAULT_BOOST,
                               source_line_id=l.line_id, created_by=s.user_id))
        added += 1
    return added


def boosts_for(db: Session, store_id: str) -> dict[str, dict[str, float]]:
    """{normalized_phrase: {sku: boost}} for the active mappings of one store."""
    out: dict[str, dict[str, float]] = {}
    for r in db.query(StoreDictionary).filter(StoreDictionary.store_id == store_id, StoreDictionary.active.is_(True)):
        out.setdefault(r.normalized_phrase, {})[r.mapped_sku] = min(MAX_BOOST, float(r.boost))
    return out
