import uuid
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Optional[dict] = None):
        self.status, self.code, self.message, self.details = status, code, message, details or {}


async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status, content={"error": {
        "code": exc.code, "message": exc.message, "details": exc.details, "request_id": f"req_{uuid.uuid4().hex[:12]}"}})
