"""MVP-FR-002 (THIN): regex-mask email + phone before anything leaves the Core.
Names/addresses in free text are NOT guaranteed to be masked — UI must say so."""
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# +45 12 34 56 78 / 12345678 / +46 70-123 45 67 ... (≥8 digits, allowing spaces/dashes)
PHONE_RE = re.compile(r"(?<![\w.])(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){7,11}\d(?!\w)(?!\.\d)")


def mask(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    # Don't treat material dimensions like "45x95" or decimals as phones: PHONE_RE needs ≥8 digits.
    text = PHONE_RE.sub("[PHONE]", text)
    return text
