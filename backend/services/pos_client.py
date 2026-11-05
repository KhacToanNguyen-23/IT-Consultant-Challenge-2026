"""Local Connector → mock-pos (simulated POS/ERP/PIM/WMS)."""
from typing import Optional

import httpx

from config import settings


class PosUnavailable(Exception):
    pass


def _client() -> httpx.Client:
    return httpx.Client(base_url=settings.mock_pos_url, timeout=settings.pos_timeout)


def _get(path: str, **params):
    try:
        with _client() as c:
            r = c.get(path, params=params)
    except httpx.HTTPError as e:
        raise PosUnavailable(str(e)) from e
    if r.status_code >= 500:
        raise PosUnavailable(f"{r.status_code}")
    r.raise_for_status()
    return r.json()


def catalog() -> tuple[list[dict], str]:
    items, cursor, version = [], None, ""
    while True:
        data = _get("/catalog", market=settings.default_market, limit=50, **({"cursor": cursor} if cursor else {}))
        items += data["items"]
        version = data["catalog_version"]
        cursor = data.get("next_cursor")
        if not cursor:
            return items, version


def customers() -> dict:
    return _get("/customers")


def stock(skus: list[str], store_id: str) -> dict[str, dict]:
    if not skus:
        return {}
    data = _get("/stock", sku=list(dict.fromkeys(skus))[:50], store_id=store_id)
    return {i["sku"]: i for i in data["items"]}


def prices(skus: list[str]) -> dict[str, float]:
    if not skus:
        return {}
    data = _get("/prices", sku=list(dict.fromkeys(skus)))
    return {i["sku"]: i["unit_price"] for i in data["items"]}


def post_order(payload: dict, idempotency_key: str) -> tuple[int, Optional[dict]]:
    """Returns (status_code, body). status 0 = transport error/timeout."""
    try:
        with _client() as c:
            r = c.post("/orders", json=payload, headers={"Idempotency-Key": idempotency_key})
        return r.status_code, (r.json() if r.content else None)
    except httpx.HTTPError:
        return 0, None


def health() -> dict:
    try:
        with _client() as c:
            return c.get("/health").json()
    except httpx.HTTPError:
        return {"status": "down"}


def admin(path: str, body: dict) -> dict:
    with _client() as c:
        r = c.post(f"/admin/{path}", json=body)
        r.raise_for_status()
        return r.json()
