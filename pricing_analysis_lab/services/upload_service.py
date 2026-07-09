from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import UploadedDataset


def save_uploaded_dataset(file_storage: FileStorage) -> UploadedDataset:
    original_name = secure_filename(file_storage.filename or "")
    if not original_name:
        raise ValueError("Please choose a CSV or XLSX file.")
    suffix = Path(original_name).suffix.lower()
    if suffix not in current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]:
        raise ValueError("Only CSV and XLSX uploads are supported.")

    stored_name = f"{uuid4()}_{original_name}"
    destination = current_app.config["UPLOAD_DIR"] / stored_name
    file_storage.save(destination)

    record = UploadedDataset(file_name=stored_name, stored_path=str(destination))
    db.session.add(record)
    db.session.commit()
    return record
