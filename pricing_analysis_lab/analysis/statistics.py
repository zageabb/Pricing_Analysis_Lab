from __future__ import annotations

from typing import Any

from pricing_analysis_lab.analysis.base import AnalysisContext, AnalysisFunction
from pricing_analysis_lab.analysis.common import dataset_to_dataframe, filter_dataframe
from pricing_analysis_lab.schemas import AnalysisPlan


class DescriptiveStatisticsFunction(AnalysisFunction):
    name = "descriptive_statistics"
    description = "Summarize numeric and categorical columns when predictive modeling is not suitable."
    supported_tasks = ("auto", "data summary/statistical analysis")
    required_inputs = ()
    output_schema = {"statistics": "object", "warnings": "array"}

    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        if context.dataset.row_count == 0:
            raise ValueError("Dataset has no rows to analyze.")

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, Any]:
        df = dataset_to_dataframe(context)
        filtered = filter_dataframe(df, context.request.filter_parameters)
        numeric = filtered.select_dtypes(include=["number"])
        categorical = filtered.select_dtypes(exclude=["number"])
        statistics: dict[str, Any] = {
            "row_count": int(filtered.shape[0]),
            "column_count": int(filtered.shape[1]),
            "numeric_summary": numeric.describe(include="all").fillna(0).to_dict() if not numeric.empty else {},
            "categorical_summary": {
                column: categorical[column].value_counts(dropna=True).head(5).to_dict()
                for column in categorical.columns
            },
        }
        warnings = []
        if filtered.shape[0] < df.shape[0]:
            warnings.append(f"Filtered to {filtered.shape[0]} rows from {df.shape[0]}.")
        return {
            "analysis_type": self.name,
            "statistics": statistics,
            "predictions": [],
            "feature_importance": [],
            "warnings": warnings,
            "model_results": {},
        }
