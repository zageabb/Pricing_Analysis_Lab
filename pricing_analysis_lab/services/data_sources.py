from __future__ import annotations

from pathlib import Path

from flask import current_app

from ..models import UploadedDataset
from .spreadsheet_loader import SpreadsheetData, load_spreadsheet


def resolve_uploaded_file(file_id: str) -> Path:
    record = UploadedDataset.query.filter_by(file_name=file_id).order_by(UploadedDataset.id.desc()).first()
    if record is not None:
        return Path(record.stored_path)
    candidate = current_app.config["UPLOAD_DIR"] / file_id
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Uploaded file '{file_id}' was not found.")


def load_request_dataset(
    file_id: str,
    sheet_name: str | None = None,
    header_row: int = 1,
) -> SpreadsheetData:
    return load_spreadsheet(resolve_uploaded_file(file_id), sheet_name=sheet_name, header_row=header_row)
