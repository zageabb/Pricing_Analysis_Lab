from __future__ import annotations

from typing import Any

from pricing_analysis_lab.analysis import get_analysis_function
from pricing_analysis_lab.analysis.base import AnalysisContext
from pricing_analysis_lab.schemas import AnalysisPlan, AnalysisRequest
from pricing_analysis_lab.services.dataset_profiler import profile_dataset
from pricing_analysis_lab.services.spreadsheet_loader import SpreadsheetData


def run_analysis_function(
    request_model: AnalysisRequest,
    dataset: SpreadsheetData,
    plan: AnalysisPlan,
) -> dict[str, Any]:
    context = AnalysisContext(
        request=request_model,
        dataset=dataset,
        dataset_profile=profile_dataset(dataset),
    )
    function = get_analysis_function(plan.selected_function)
    function.validate(context, plan)
    return function.run(context, plan)
