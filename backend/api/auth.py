"""MVP-FR-032: POST /auth/login, POST /auth/logout, GET /auth/me (simulated sign-in, SRS section 7.1)."""
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from api.common import ApiError, StrictBody
from config import settings
from db.database import get_db
from db.models import DemoUser
from i18n import t
from services import auth

router = APIRouter(prefix="/api/v1/auth", tags=["Auth (simulated)"])


class LoginBody(StrictBody):
    username: str
    password: str


def _profile(u: DemoUser) -> dict:
    return {"user_id": u.user_id, "store_id": u.store_id, "display_name": u.display_name,
            "idle_timeout_seconds": settings.idle_timeout_seconds, "simulated": True}


def _set_cookie(response: Response, user_id: str) -> None:
    response.set_cookie(auth.COOKIE, auth.make_token(user_id), max_age=settings.idle_timeout_seconds, httponly=True, samesite="lax", path="/")


@router.post("/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)):
    if not settings.demo_password:
        raise ApiError(503, "LOGIN_DISABLED", t("login_disabled"))
    u = db.get(DemoUser, body.username)
    # same answer for "no such user", "inactive" and "wrong password": do not reveal which accounts exist
    if u is None or not u.active or not auth.verify_password(body.password, u.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", t("login_failed"))
    _set_cookie(response, u.user_id)
    return _profile(u)


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(auth.COOKIE, path="/")


@router.get("/me")
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    user_id = auth.user_from_request(request)
    u = db.get(DemoUser, user_id) if user_id else None
    if u is None or not u.active:
        raise ApiError(401, "UNAUTHENTICATED", t("unauthenticated"))
    _set_cookie(response, u.user_id)  # sliding idle window
    return _profile(u)
