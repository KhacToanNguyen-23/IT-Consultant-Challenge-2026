import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import i18n
from fastapi.middleware.cors import CORSMiddleware

from ai import embedding
from api import auth as auth_api, catalog, quotes, sessions
from fastapi.exceptions import RequestValidationError

from sqlalchemy.exc import InterfaceError, OperationalError

from api.common import (ApiError, _envelope, api_error_handler, db_unavailable_handler, unexpected_error_handler,
                        validation_error_handler)
from config import settings
from db.database import SessionLocal, init_db
from services import auth, seed

log = logging.getLogger("sitedesk")

app = FastAPI(
    title="SiteDesk Core API",
    description="AI-Assisted Trade Counter Engine for Company A (DK/NO/SE). POS/ERP/catalog/stock/price are simulated.",
    version="0.2.0",
)


@app.middleware("http")
async def unexpected_errors(request: Request, call_next):
    """Registered before CORS so it runs inside it. Otherwise a 500 has no CORS headers and the browser reports a network failure."""
    try:
        return await call_next(request)
    except Exception:  # noqa: BLE001
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL", "message": i18n.t("internal_error"), "details": {}}})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(OperationalError, db_unavailable_handler)
app.add_exception_handler(InterfaceError, db_unavailable_handler)
app.add_exception_handler(Exception, unexpected_error_handler)


@app.middleware("http")
async def language(request: Request, call_next):
    """UI language per request: header X-Lang, or ?lang= (print pages opened in a new tab)."""
    i18n.set_lang(request.query_params.get("lang") or request.headers.get("x-lang"))
    return await call_next(request)


@app.middleware("http")
async def require_login_when_enabled(request: Request, call_next):
    """AUTH_REQUIRED=true: every /api/v1 call except /auth/*, /health and CORS preflight needs a valid demo session (FR-032)."""
    path = request.url.path
    guarded = (settings.auth_required and path.startswith("/api/v1/") and not path.startswith("/api/v1/auth/")
               and path != "/api/v1/health" and request.method != "OPTIONS")
    if guarded and auth.user_from_request(request) is None:
        return _envelope(401, "UNAUTHENTICATED", i18n.t("unauthenticated"))
    return await call_next(request)


app.include_router(auth_api.router)
app.include_router(sessions.router)
app.include_router(quotes.router)
app.include_router(catalog.router)


@app.on_event("startup")
def startup() -> None:
    init_db()
    with SessionLocal() as db:
        seed.ensure_reference(db)
        for attempt in range(10):  # mock-pos may still be booting
            try:
                log.warning("catalog sync: %s", seed.sync_from_pos(db))
                break
            except Exception as e:  # noqa: BLE001
                db.rollback()
                log.warning("catalog sync failed (%s), retrying", e)
                time.sleep(2)

    def _reindex_missing():
        from services import retrieval
        with SessionLocal() as db:
            log.warning("embedding reindex: %s products", retrieval.reindex(db, only_missing=True))

    embedding.load_in_background(after=_reindex_missing)


@app.get("/", tags=["General"])
def root():
    return {"message": "Welcome to SiteDesk Core API", "docs_url": "/docs", "version": app.version}


@app.get("/api/health", tags=["General"])
def legacy_health():
    from db.database import SessionLocal as _S
    from api.catalog import health
    with _S() as db:
        return health(db)
