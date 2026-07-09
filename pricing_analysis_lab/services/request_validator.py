from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from ..schemas import AnalysisRequest


def validate_analysis_request(payload: dict[str, Any]) -> AnalysisRequest:
    return AnalysisRequest.model_validate(payload)


def collect_validation_errors(payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        validate_analysis_request(payload)
    except ValidationError as exc:
        return exc.errors(include_url=False)
    return []
