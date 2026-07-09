from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from ..schemas import AnalysisResponse, ErrorItem
from .analysis_runner import run_analysis_function
from .data_sources import load_request_dataset
from .dataset_profiler import profile_dataset
from .orchestrator import create_analysis_plan, interpret_analysis_result
from .request_validator import validate_analysis_request
from .run_history import complete_run, create_run


def analyse_payload(payload: dict[str, Any]) -> dict[str, Any]:
    run = create_run(payload)
    try:
        request_model = validate_analysis_request(payload)
        dataset = load_request_dataset(
            request_model.data_source.file_id,
            sheet_name=request_model.data_source.sheet_name,
            header_row=request_model.data_source.header_row,
        )
        dataset_profile = profile_dataset(dataset)
        _validate_request_against_dataset(request_model, dataset_profile)
        plan = create_analysis_plan(request_model, dataset_profile)
        result = run_analysis_function(request_model, dataset, plan)
        interpretation = interpret_analysis_result(result, plan, dataset_profile)

        response = AnalysisResponse(
            status="success",
            request_id=run.request_id,
            analysis_type=result["analysis_type"],
            dataset_profile=dataset_profile,
            llm_plan=plan.model_dump(),
            model_results=result.get("model_results", {}),
            statistics=result.get("statistics", {}),
            predictions=result.get("predictions", []),
            feature_importance=result.get("feature_importance", []),
            interpretation=interpretation,
            warnings=result.get("warnings", []),
            errors=[],
        )
        complete_run(run, "success", response.analysis_type, response.model_dump())
        return response.model_dump()
    except ValidationError as exc:
        response = AnalysisResponse(
            status="error",
            request_id=run.request_id,
            errors=[ErrorItem(stage="request_validation", message=str(exc))],
        )
        complete_run(run, "error", None, response.model_dump())
        return response.model_dump()
    except Exception as exc:  # noqa: BLE001
        response = AnalysisResponse(
            status="error",
            request_id=run.request_id,
            errors=[ErrorItem(stage="analysis", message=str(exc))],
        )
        complete_run(run, "error", None, response.model_dump())
        return response.model_dump()


def _validate_request_against_dataset(request_model, dataset_profile: dict[str, Any]) -> None:
    dataset_columns = {column["name"] for column in dataset_profile.get("columns", [])}
    missing_targets = [field for field in request_model.target_fields if field not in dataset_columns]
    if missing_targets:
        raise ValueError(f"Target field(s) not found: {', '.join(missing_targets)}")
