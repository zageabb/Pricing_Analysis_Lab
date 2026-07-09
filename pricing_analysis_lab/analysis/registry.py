from __future__ import annotations

from pricing_analysis_lab.analysis.base import AnalysisFunction
from pricing_analysis_lab.analysis.random_forest import (
    RandomForestClassificationFunction,
    RandomForestRegressionFunction,
)
from pricing_analysis_lab.analysis.search import FilteredSearchFunction
from pricing_analysis_lab.analysis.statistics import DescriptiveStatisticsFunction


ANALYSIS_FUNCTIONS: dict[str, AnalysisFunction] = {
    "random_forest_regression": RandomForestRegressionFunction(),
    "random_forest_classification": RandomForestClassificationFunction(),
    "descriptive_statistics": DescriptiveStatisticsFunction(),
    "filtered_search": FilteredSearchFunction(),
}


def get_analysis_function(name: str) -> AnalysisFunction:
    try:
        return ANALYSIS_FUNCTIONS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown analysis function: {name}") from exc
