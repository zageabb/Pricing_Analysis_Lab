from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TaskType = Literal[
    "auto",
    "prediction",
    "classification",
    "regression",
    "similarity/search",
    "data summary/statistical analysis",
]


class DataSourceConfig(BaseModel):
    type: Literal["uploaded_file"]
    file_id: str = Field(min_length=1)
    sheet_name: str | None = None
    header_row: int = Field(default=1, ge=1)


class ModelPreferences(BaseModel):
    preferred_model: str = "auto"
    allow_llm_to_tune: bool = True
    forced_analysis_function: str = "auto"


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_source: DataSourceConfig
    task: TaskType = "auto"
    parameter_fields: list[str] = Field(default_factory=list)
    input_parameters: dict[str, Any] = Field(default_factory=dict)
    target_fields: list[str] = Field(default_factory=list)
    output_fields: list[str] = Field(default_factory=list)
    prediction_target_fields: list[str] = Field(default_factory=list)
    excluded_fields: list[str] = Field(default_factory=list)
    filter_parameters: dict[str, Any] = Field(default_factory=dict)
    model_preferences: ModelPreferences = Field(default_factory=ModelPreferences)
    response_format: Literal["human", "json", "human_and_json"] = "human_and_json"
    auto_run: bool = False

    @field_validator(
        "parameter_fields",
        "target_fields",
        "output_fields",
        "prediction_target_fields",
        "excluded_fields",
        mode="before",
    )
    @classmethod
    def normalize_string_lists(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("Expected a list of field names.")
        normalized = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    @model_validator(mode="after")
    def validate_field_intent(self) -> "AnalysisRequest":
        if not self.target_fields and self.task in {"prediction", "classification", "regression"}:
            raise ValueError("Target fields are required for supervised tasks.")
        if self.prediction_target_fields and self.target_fields:
            combined = set(self.prediction_target_fields) & set(self.target_fields)
            if combined:
                raise ValueError("Prediction target fields should not duplicate target fields.")
        return self


class PreprocessingPlan(BaseModel):
    handle_missing: str = "median_or_unknown"
    encode_categoricals: bool = True
    scale_numeric: bool = False


class ValidationPlan(BaseModel):
    use_train_test_split: bool = True
    use_cross_validation: bool = False


class AnalysisPlan(BaseModel):
    selected_function: str
    reason: str
    target_field: str | None = None
    feature_fields: list[str] = Field(default_factory=list)
    preprocessing: PreprocessingPlan = Field(default_factory=PreprocessingPlan)
    model_settings: dict[str, Any] = Field(default_factory=dict)
    validation: ValidationPlan = Field(default_factory=ValidationPlan)


class InterpretationPayload(BaseModel):
    summary: str = ""
    reasons: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)


class ErrorItem(BaseModel):
    stage: str
    message: str


class AnalysisResponse(BaseModel):
    status: Literal["success", "error"]
    request_id: str
    analysis_type: str | None = None
    dataset_profile: dict[str, Any] = Field(default_factory=dict)
    llm_plan: dict[str, Any] = Field(default_factory=dict)
    model_results: dict[str, Any] = Field(default_factory=dict)
    statistics: dict[str, Any] = Field(default_factory=dict)
    predictions: list[Any] = Field(default_factory=list)
    feature_importance: list[Any] = Field(default_factory=list)
    interpretation: InterpretationPayload = Field(default_factory=InterpretationPayload)
    warnings: list[str] = Field(default_factory=list)
    errors: list[ErrorItem] = Field(default_factory=list)


def request_schema() -> dict[str, Any]:
    return AnalysisRequest.model_json_schema()


def response_schema() -> dict[str, Any]:
    return AnalysisResponse.model_json_schema()
