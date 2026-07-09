from __future__ import annotations

from datetime import UTC, datetime

from .extensions import db


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class PromptTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    path = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UploadedDataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    sheet_name = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class AnalysisRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending")
    analysis_type = db.Column(db.String(120), nullable=True)
    request_json = db.Column(db.Text, nullable=False)
    response_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
