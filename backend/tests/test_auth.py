"""MVP-FR-032 / NFR-002: simulated sign-in. Not SSO; passwords only from the environment; the counter works without it."""
import pytest

from services import auth


# ------------------------------------------------------------------ unit
def test_password_is_hashed_salted_and_verified():
    h1, h2 = auth.hash_password("s3cret"), auth.hash_password("s3cret")
    assert h1 != h2 and "s3cret" not in h1  # random salt, plain text never stored
    assert auth.verify_password("s3cret", h1) and not auth.verify_password("S3cret", h1)


@pytest.mark.parametrize("stored", ["!disabled", "", "plaintext", "pbkdf2$x$y$z", "pbkdf2$1$zz$00"])
def test_unusable_hashes_never_verify(stored):
    assert auth.verify_password("anything", stored) is False


def test_token_round_trip_expiry_and_tampering():
    token = auth.make_token("EMP-1042", ttl=300, now=1000)
    assert auth.read_token(token, now=1100) == "EMP-1042"
    assert auth.read_token(token, now=1301) is None  # idle window over
    payload, sig = token.split(".")
    assert auth.read_token(f"{payload}.{'0' * len(sig)}", now=1100) is None  # forged signature
    forged = auth.make_token("EMP-9999", ttl=300, now=1000).split(".")[0]
    assert auth.read_token(f"{forged}.{sig}", now=1100) is None  # signature of another payload
    for junk in (None, "", "no-dot", "a.b", "..."):
        assert auth.read_token(junk) is None


# ------------------------------------------------------------------ integration (needs Postgres, see conftest)
def _login(client, user="EMP-1042", password="test-only-password"):
    return client.post("/api/v1/auth/login", json={"username": user, "password": password})


def test_login_logout_and_me(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    r = _login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "EMP-1042" and body["idle_timeout_seconds"] == 300 and body["simulated"] is True
    assert "password" not in r.text and "test-only-password" not in r.text
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/v1/auth/me").json()["display_name"] == "Demo Associate"
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_wrong_password_and_unknown_user_look_identical(client):
    wrong = _login(client, password="nope")
    unknown = _login(client, user="EMP-0000")
    for r in (wrong, unknown):
        assert r.status_code == 401 and r.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]  # no account enumeration


def test_login_is_disabled_when_no_demo_password_is_configured(client):
    from config import settings

    settings.demo_password = ""
    r = _login(client)
    assert r.status_code == 503 and r.json()["error"]["code"] == "LOGIN_DISABLED"


def test_only_the_password_hash_reaches_the_database(client, app_env):
    from db.database import SessionLocal
    from db.models import DemoUser

    with SessionLocal() as db:
        users = {u.user_id: u.password_hash for u in db.query(DemoUser)}
    assert {"EMP-1042", "EMP-2077"} <= set(users)
    assert all(h.startswith("pbkdf2$") and "test-only-password" not in h for h in users.values())


def test_an_expired_session_cookie_is_rejected(client):
    client.cookies.set(auth.COOKIE, auth.make_token("EMP-1042", ttl=300, now=0))  # expired long ago
    assert client.get("/api/v1/auth/me").status_code == 401


def test_enforcement_is_off_by_default_so_the_counter_works_without_login(client):
    assert client.post("/api/v1/sessions", json={"input_type": "paste_text", "market": "DK"}).status_code == 200


def test_when_required_every_api_call_needs_a_session_except_health_and_auth(client):
    from config import settings

    settings.auth_required = True
    r = client.post("/api/v1/sessions", json={"input_type": "paste_text", "market": "DK"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED" and r.json()["error"]["request_id"].startswith("req_")
    assert client.get("/api/v1/health").status_code == 200  # monitoring stays open
    assert _login(client).status_code == 200
    assert client.post("/api/v1/sessions", json={"input_type": "paste_text", "market": "DK"}).status_code == 200


def test_the_signed_in_associate_is_recorded_on_the_order(client, counter):
    _login(client, user="EMP-2077")
    sid = counter.open("120 m timber 45x95 C24")
    counter.analyze(sid)
    counter.resolve_all(sid)
    out = counter.confirm(sid).json()
    assert out["payload"]["confirmed_by_associate"] == "EMP-2077"  # accountability: who confirmed, not a fixed user
