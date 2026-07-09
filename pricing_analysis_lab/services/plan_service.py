from __future__ import annotations

from typing import Any

from .data_sources import load_request_dataset
from .dataset_profiler import profile_dataset
from .orchestrator import create_analysis_plan
from .request_validator import validate_analysis_request


def build_plan_preview(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    request_model = validate_analysis_request(payload)
    dataset = load_request_dataset(
        request_model.data_source.file_id,
        sheet_name=request_model.data_source.sheet_name,
    )
    dataset_profile = profile_dataset(dataset)
    plan = create_analysis_plan(request_model, dataset_profile)
    return dataset_profile, plan.model_dump()
