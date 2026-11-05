import logging
import uuid
from typing import Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import InterfaceError, OperationalError

from i18n import t

log = logging.getLogger("sitedesk.api")


class StrictBody(BaseModel):
    """Request body that rejects unknown fields: a typo like `quantity` for `requested_qty` must be a 422, not a silent no-op."""
    model_config = ConfigDict(extra="forbid")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Optional[dict] = None):
        self.status, self.code, self.message, self.details = status, code, message, details or {}


async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status, content={"error": {
        "code": exc.code, "message": exc.message, "details": exc.details, "request_id": f"req_{uuid.uuid4().hex[:12]}"}})


def _envelope(status: int, code: str, message: str, details: Optional[dict] = None, request_id: Optional[str] = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "details": details or {}, "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}"}})


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """SRS §7: every 4xx/5xx uses the same error envelope (FastAPI's default {"detail": [...]} is not it)."""
    fields = [{"field": ".".join(str(x) for x in e.get("loc", ())[1:]), "problem": e.get("type", "invalid")} for e in exc.errors()]
    return _envelope(422, "VALIDATION", t("bad_request_body"), {"fields": fields})


async def unexpected_error_handler(request: Request, exc: Exception):
    """Last resort: never leak a stack trace or a bare 'Internal Server Error' to the counter UI."""
    rid = f"req_{uuid.uuid4().hex[:12]}"
    log.error("unhandled error on %s %s (%s): %r", request.method, request.url.path, rid, exc, exc_info=exc)
    return _envelope(500, "INTERNAL", t("internal_error"), request_id=rid)


async def db_unavailable_handler(request: Request, exc: Exception):
    """SRS §7: 503 for a dependency that is down (database), with the same envelope; never a stack trace."""
    rid = f"req_{uuid.uuid4().hex[:12]}"
    log.error("database unavailable on %s %s (%s): %s", request.method, request.url.path, rid, str(exc)[:200])
    return _envelope(503, "DB_UNAVAILABLE", t("db_unavailable"), request_id=rid)
