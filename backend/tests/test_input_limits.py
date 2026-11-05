"""OI-04 input limits, XLSX handling, and regression guards for the parser regexes."""
import io

import pytest

from services import parser


def _pdf(pages: int) -> bytes:
    pypdf = pytest.importorskip("pypdf")
    w = pypdf.PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_pdf_over_the_page_limit_is_rejected_with_its_numbers():
    with pytest.raises(parser.InputTooLarge) as e:
        parser.pdf_text(_pdf(parser.MAX_PDF_PAGES + 1))
    assert e.value.code == "pdf_too_long" and e.value.params == {"pages": parser.MAX_PDF_PAGES + 1, "max": parser.MAX_PDF_PAGES}


def test_pdf_at_the_page_limit_is_read():
    assert parser.pdf_text(_pdf(parser.MAX_PDF_PAGES)) == "\n" * (parser.MAX_PDF_PAGES - 1)


def test_row_limit():
    parser.check_row_limit(parser.MAX_ROWS)
    with pytest.raises(parser.InputTooLarge) as e:
        parser.check_row_limit(parser.MAX_ROWS + 1)
    assert e.value.code == "too_many_rows" and e.value.params["max"] == parser.MAX_ROWS


def _xlsx(*sheets):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for i, rows in enumerate(sheets, 1):
        ws = wb.create_sheet(f"S{i}")
        for r in rows:
            ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_xlsx_reads_every_sheet_so_nothing_is_silently_ignored():
    data = _xlsx([("Vare", "Antal"), ("timber 45x95 C24", 120)], [("Item", "Qty"), ("cement 25 kg", 5)])
    assert parser.rows_from_table(data, "order.xlsx").splitlines() == ["timber 45x95 C24 120", "cement 25 kg 5"]


def test_xlsx_keeps_a_first_row_that_is_data_not_a_header():
    data = _xlsx([("timber 45x95 C24", 120)])
    assert parser.rows_from_table(data, "order.xlsx") == "timber 45x95 C24 120"


def test_csv_header_row_is_dropped_and_semicolons_work():
    out = parser.rows_from_table(b"vare;antal\ntimber 45x95 C24;120\ncement 25 kg;5\n", "order.csv")
    assert out.splitlines() == ["timber 45x95 C24 120", "cement 25 kg 5"]


def test_header_and_accessory_regexes_use_word_boundaries():
    # guards against the escape bug where "\b" became a backspace character
    assert "\x08" not in parser.HEADER_RE.pattern and "\x08" not in parser.ACCESSORY_RE.pattern
    assert parser.HEADER_RE.search("Vare antal") and not parser.HEADER_RE.search("hardware antalya")
    assert parser.ACCESSORY_RE.search(" 100 søm ") and parser.ACCESSORY_RE.search("nail 4x100")
    assert not parser.ACCESSORY_RE.search("thumbnail sheet")  # "nail" inside another word


# --- a material line that carries a contact detail must not disappear (silent data loss) ---
def test_material_line_with_a_masked_phone_or_email_is_kept_and_cleaned():
    rows = parser.split_text("Hej\n120 m timber 45x95 C24 ring [PHONE] eller [EMAIL]\nRing på [PHONE].\n[EMAIL] ... 10 stk timber 45x95 C24")
    assert [r.quantity for r in rows] == [120, 10]
    assert all("[PHONE]" not in (r.item_text or "") and "[EMAIL]" not in (r.item_text or "") for r in rows)
    assert rows[0].source_text.endswith("[EMAIL]")  # the source text keeps the (masked) original for the preview


def test_pure_contact_lines_are_still_skipped():
    assert parser.split_text("Ring på [PHONE].\nTlf: [PHONE]\nkunde: [EMAIL]\n") == []
