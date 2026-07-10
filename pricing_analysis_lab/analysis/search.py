from __future__ import annotations

from typing import Any

from pricing_analysis_lab.analysis.base import AnalysisContext, AnalysisFunction
from pricing_analysis_lab.analysis.common import dataset_to_dataframe, filter_dataframe
from pricing_analysis_lab.schemas import AnalysisPlan


class FilteredSearchFunction(AnalysisFunction):
    name = "filtered_search"
    description = "Return rows that match supplied input parameters."
    supported_tasks = ("auto", "similarity/search")
    required_inputs = ()
    output_schema = {"predictions": "array"}

    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        if not context.request.input_parameters:
            raise ValueError("Input parameters are required for filtered search.")

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        df = dataset_to_dataframe(context)
        filtered = filter_dataframe(df, context.request.input_parameters)
        output_fields = context.request.output_fields or context.dataset.columns
        visible = filtered[output_fields] if len(filtered) else filtered
        return {
            "analysis_type": self.name,
            "statistics": {"matching_rows": int(filtered.shape[0])},
            "predictions": [
                {"prediction_scope": "match", **row}
                for row in visible.head(10).to_dict(orient="records")
            ],
            "feature_importance": [],
            "warnings": [] if filtered.shape[0] else ["No rows matched the supplied parameters."],
            "model_results": {},
        }
