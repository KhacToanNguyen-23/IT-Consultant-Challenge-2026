import csv
import io
import re
from pathlib import Path

from fastapi import HTTPException, UploadFile
from openpyxl import load_workbook
from pypdf import PdfReader


async def extract_lines(file: UploadFile | None, raw_text: str | None) -> list[str]:
    if bool(file) == bool(raw_text and raw_text.strip()):
        raise HTTPException(400, "Provide exactly one of 'file' or 'raw_text'.")
    if raw_text:
        lines = raw_text.splitlines()
    else:
        assert file is not None
        suffix = Path(file.filename or "").suffix.lower()
        content = await file.read()
        try:
            if suffix == ".pdf":
                text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
                lines = text.splitlines()
            elif suffix == ".xlsx":
                book = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
                sheet = book.active
                lines = [" ".join(str(value) for value in row if value is not None) for row in sheet.iter_rows(values_only=True)]
                book.close()
            elif suffix == ".csv":
                lines = [" ".join(row) for row in csv.reader(io.StringIO(content.decode("utf-8-sig")))]
            else:
                raise HTTPException(415, "Supported file types: .pdf, .xlsx, .csv")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(422, f"Could not parse uploaded file: {exc}") from exc
    cleaned = [re.sub(r"\s+", " ", line).strip() for line in lines]
    cleaned = [line for line in cleaned if line]
    if not cleaned:
        raise HTTPException(422, "No item lines were found in the input.")
    return cleaned
