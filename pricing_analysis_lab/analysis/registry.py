from __future__ import annotations

from pricing_analysis_lab.analysis.base import AnalysisFunction
from pricing_analysis_lab.analysis.gradient_boosting import (
    GradientBoostingClassificationFunction,
    GradientBoostingRegressionFunction,
)
from pricing_analysis_lab.analysis.linear_models import LinearRegressionFunction
from pricing_analysis_lab.analysis.random_forest import (
    RandomForestClassificationFunction,
    RandomForestRegressionFunction,
)
from pricing_analysis_lab.analysis.search import FilteredSearchFunction
from pricing_analysis_lab.analysis.similarity import NearestNeighborSimilarityFunction
from pricing_analysis_lab.analysis.statistics import DescriptiveStatisticsFunction


ANALYSIS_FUNCTIONS: dict[str, AnalysisFunction] = {
    "linear_regression": LinearRegressionFunction(),
    "random_forest_regression": RandomForestRegressionFunction(),
    "gradient_boosting_regression": GradientBoostingRegressionFunction(),
    "random_forest_classification": RandomForestClassificationFunction(),
    "gradient_boosting_classification": GradientBoostingClassificationFunction(),
    "descriptive_statistics": DescriptiveStatisticsFunction(),
    "nearest_neighbor_similarity": NearestNeighborSimilarityFunction(),
    "filtered_search": FilteredSearchFunction(),
}


def get_analysis_function(name: str) -> AnalysisFunction:
    try:
        return ANALYSIS_FUNCTIONS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown analysis function: {name}") from exc
