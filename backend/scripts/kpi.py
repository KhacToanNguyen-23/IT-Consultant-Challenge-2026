"""Run the three KPI queries (SRS v2 section 10) and print them.   python -m scripts.kpi"""
import re
from pathlib import Path

from sqlalchemy import text

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "kpi.sql"


def load_queries() -> dict[str, str]:
    """{name: sql} from sql/kpi.sql (blocks start with '-- name: <id>')."""
    parts = re.split(r"^-- name:\s*(\w+)\s*$", SQL_FILE.read_text(encoding="utf-8"), flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def run_all(db) -> dict[str, dict]:
    return {name: dict(db.execute(text(sql)).mappings().one()) for name, sql in load_queries().items()}


if __name__ == "__main__":
    from db.database import SessionLocal

    with SessionLocal() as session:
        for name, row in run_all(session).items():
            print(f"{name}: " + ", ".join(f"{k}={v if v is None else (round(float(v), 3) if not isinstance(v, int) else v)}" for k, v in row.items()))
