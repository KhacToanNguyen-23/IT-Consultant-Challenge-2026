"""MVP-FR-032 (THIN): a clearly simulated sign-in. NOT SSO and not production security.

* Passwords are never stored in the repo: the demo password comes from the DEMO_PASSWORD environment variable and only a
  PBKDF2 hash reaches the database. Without it, login is disabled (the counter keeps working with the default associate).
* The session is a signed token (user | expiry | HMAC) in an HttpOnly cookie. Every authenticated request renews it, so the
  idle timeout (default 300 s) is a sliding window.
"""
import base64
import hashlib
import hmac
import os
import time
from typing import Optional

from fastapi import Request

from config import settings

COOKIE = "sitedesk_session"
ITERATIONS = 120_000


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = stored.split("$")
        if scheme != "pbkdf2":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):  # "!disabled", malformed values, ...
        return False


def _sign(payload: str) -> str:
    return hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_token(user_id: str, ttl: Optional[int] = None, now: Optional[float] = None) -> str:
    expires = int((now if now is not None else time.time()) + (ttl if ttl is not None else settings.idle_timeout_seconds))
    payload = base64.urlsafe_b64encode(f"{user_id}|{expires}".encode()).decode()
    return f"{payload}.{_sign(payload)}"


def read_token(token: Optional[str], now: Optional[float] = None) -> Optional[str]:
    """The user id of a valid, unexpired token, else None."""
    try:
        payload, sig = (token or "").split(".", 1)
        if not hmac.compare_digest(sig, _sign(payload)):
            return None
        user_id, expires = base64.urlsafe_b64decode(payload.encode()).decode().rsplit("|", 1)
        return user_id if int(expires) > (now if now is not None else time.time()) else None
    except (ValueError, TypeError):
        return None


def user_from_request(request: Request) -> Optional[str]:
    return read_token(request.cookies.get(COOKIE))
