from __future__ import annotations

from sklearn.neighbors import NearestNeighbors

from pricing_analysis_lab.analysis.base import AnalysisContext, AnalysisFunction
from pricing_analysis_lab.analysis.common import dataset_to_dataframe, resolve_feature_fields
from pricing_analysis_lab.analysis.supervised import build_supervised_pipeline, prediction_input
from pricing_analysis_lab.schemas import AnalysisPlan


class NearestNeighborSimilarityFunction(AnalysisFunction):
    name = "nearest_neighbor_similarity"
    description = "Return nearest matching rows using encoded feature similarity."
    supported_tasks = ("auto", "similarity/search")
    required_inputs = ()
    output_schema = {"predictions": "array", "statistics": "object"}

    def validate(self, context: AnalysisContext, plan: AnalysisPlan) -> None:
        if not context.request.input_parameters:
            raise ValueError("Input parameters are required for similarity search.")
        if context.dataset.row_count < 3:
            raise ValueError("At least three rows are required for similarity search.")

    def run(self, context: AnalysisContext, plan: AnalysisPlan) -> dict[str, object]:
        feature_fields = resolve_feature_fields(context)
        df = dataset_to_dataframe(context)
        frame = df[feature_fields].copy()
        pipeline = build_supervised_pipeline(
            frame.assign(_dummy_target=0),
            feature_fields,
            NearestNeighbors(n_neighbors=min(5, len(frame))),
            scale_numeric=True,
            sparse_output=False,
        )
        transformed = pipeline.named_steps["preprocessor"].fit_transform(frame)
        model = pipeline.named_steps["model"]
        model.fit(transformed)

        incoming = prediction_input(feature_fields, context.request.input_parameters)
        encoded_input = pipeline.named_steps["preprocessor"].transform(incoming)
        distances, indices = model.kneighbors(encoded_input)
        output_fields = context.request.output_fields or context.dataset.columns

        predictions = []
        for distance, index in zip(distances[0], indices[0], strict=True):
            row = df.iloc[int(index)]
            payload = {field: row[field] for field in output_fields if field in row.index}
            payload["prediction_scope"] = "match"
            payload["similarity_distance"] = float(distance)
            predictions.append(payload)

        return {
            "analysis_type": self.name,
            "statistics": {"match_count": len(predictions)},
            "predictions": predictions,
            "feature_importance": [],
            "warnings": [],
            "model_results": {"feature_fields": feature_fields},
        }
