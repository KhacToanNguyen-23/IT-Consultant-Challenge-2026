"""MVP-FR-002 (THIN): regex-mask email + phone before anything leaves the Core.
Names/addresses in free text are NOT guaranteed to be masked — UI must say so."""
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# +45 12 34 56 78 / +1 (415) 555-0123 ext. 42 / 12345678 ... (7-15 digits; separators, brackets and extension allowed)
PHONE_RE = re.compile(
    r"(?<![\w.])(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{1,4}\)?[\s.-]?){2,5}\d{2,4}(?:\s*(?:ext\.?|x)\s*\d{1,6})?(?!\w)(?!\.\d)",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"\s*(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\s*")


def _mask_phone(match: re.Match) -> str:
    if DATE_RE.fullmatch(match.group()):  # 04-11-2026 is a date, not a phone number
        return match.group()
    digits = sum(c.isdigit() for c in match.group())
    return "[PHONE]" if 7 <= digits <= 15 else match.group()


def mask(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    # Material dimensions like "45x95" or decimals like "12.5" have <7 digits, so they stay intact.
    return PHONE_RE.sub(_mask_phone, text)
