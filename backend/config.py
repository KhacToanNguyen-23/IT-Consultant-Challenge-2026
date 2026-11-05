import os
import secrets


def _f(name: str, default: str) -> float:
    return float(os.getenv(name, default))


class Settings:
    database_url = os.getenv("DATABASE_URL", "")
    mock_pos_url = os.getenv("MOCK_POS_URL", "http://mock-pos:8001")
    connector_mode = os.getenv("CONNECTOR_MODE", "api")  # api | csv
    default_market = os.getenv("DEFAULT_MARKET", "DK")
    default_store = os.getenv("DEFAULT_STORE_ID", "DK-CPH-04")
    default_user = os.getenv("DEFAULT_USER_ID", "EMP-1042")  # mock login cut (SRS §0.3 rule 2): one hard-coded user
    # Simulated sign-in (FR-032). AUTH_REQUIRED=false keeps the single default associate so nothing else depends on it.
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
    demo_password = os.getenv("DEMO_PASSWORD", "")  # never stored in the repo; empty = login disabled
    session_secret = os.getenv("SESSION_SECRET", "") or secrets.token_hex(32)  # per process when unset
    idle_timeout_seconds = int(os.getenv("IDLE_TIMEOUT_SECONDS", "300"))
    high_threshold = _f("MATCH_HIGH_THRESHOLD", "0.90")
    review_threshold = _f("MATCH_REVIEW_THRESHOLD", "0.80")
    ambiguity_gap = _f("AMBIGUITY_GAP", "0.05")
    pos_timeout = _f("MOCK_POS_TIMEOUT_SECONDS", "2")
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001").split(",") if o.strip()]


settings = Settings()

# Runtime toggle (FR-033). Starts from env, can be flipped from the demo UI.
runtime = {"ai_fail_mode": os.getenv("AI_FAIL_MODE", "false").lower() == "true"}

# UI texts live in i18n.py
