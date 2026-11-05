"""SRS §7 error envelope and damaged-upload handling (NFR-06: the counter never meets a bare 500)."""
import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from api.common import ApiError, api_error_handler, unexpected_error_handler, validation_error_handler
from fastapi.exceptions import RequestValidationError
from services import parser


class Body(BaseModel):
    qty: int


def _app() -> TestClient:
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)

    @app.post("/validate")
    def validate(body: Body):
        return {"ok": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret internals: password=hunter2")

    @app.get("/known")
    def known():
        raise ApiError(409, "UNRESOLVED_LINES", "Lines need a choice", {"line_nos": [3]})

    return TestClient(app, raise_server_exceptions=False)


def _assert_envelope(r, status, code):
    assert r.status_code == status
    err = r.json()["error"]
    assert err["code"] == code and err["request_id"].startswith("req_")
    assert set(err) == {"code", "message", "details", "request_id"}
    return err


def test_known_errors_use_the_standard_envelope():
    err = _assert_envelope(_app().get("/known"), 409, "UNRESOLVED_LINES")
    assert err["details"] == {"line_nos": [3]}


def test_validation_errors_use_the_same_envelope_not_fastapi_detail():
    r = _app().post("/validate", json={"qty": "many"})
    err = _assert_envelope(r, 422, "VALIDATION")
    assert "detail" not in r.json() and err["details"]["fields"]


def test_unexpected_errors_never_leak_internals():
    r = _app().get("/boom")
    err = _assert_envelope(r, 500, "INTERNAL")
    assert "hunter2" not in r.text and "RuntimeError" not in r.text and "Traceback" not in r.text
    assert err["message"]


def test_damaged_pdf_is_reported_as_unreadable_not_crash():
    with pytest.raises(parser.UnreadableFile):
        parser.pdf_text(b"%PDF-1.4\n%%EOF")
    with pytest.raises(parser.UnreadableFile):
        parser.pdf_text(b"%PDF-1.4 garbage" * 50)


def test_blank_valid_pdf_has_no_text_so_ingest_can_answer_scan_only():
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    assert parser.pdf_text(buf.getvalue()).strip() == ""
