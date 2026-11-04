import os


def _f(name: str, default: str) -> float:
    return float(os.getenv(name, default))


class Settings:
    database_url = os.getenv("DATABASE_URL", "")
    mock_pos_url = os.getenv("MOCK_POS_URL", "http://mock-pos:8001")
    connector_mode = os.getenv("CONNECTOR_MODE", "api")  # api | csv
    default_market = os.getenv("DEFAULT_MARKET", "DK")
    default_store = os.getenv("DEFAULT_STORE_ID", "DK-CPH-04")
    default_user = os.getenv("DEFAULT_USER_ID", "EMP-1042")  # mock login cut (SRS §0.3 rule 2): one hard-coded user
    high_threshold = _f("MATCH_HIGH_THRESHOLD", "0.90")
    review_threshold = _f("MATCH_REVIEW_THRESHOLD", "0.80")
    ambiguity_gap = _f("AMBIGUITY_GAP", "0.05")
    pos_timeout = _f("MOCK_POS_TIMEOUT_SECONDS", "2")
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]


settings = Settings()

# Runtime toggle (FR-033). Starts from env, can be flipped from the demo UI.
runtime = {"ai_fail_mode": os.getenv("AI_FAIL_MODE", "false").lower() == "true"}

# UI texts live in i18n.py
