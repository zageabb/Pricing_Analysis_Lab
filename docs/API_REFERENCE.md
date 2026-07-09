# API Reference

## Overview

The primary machine-facing endpoint is:

```text
POST /api/analyse
```

The application also exposes schema endpoints:

- `GET /api/schema/request`
- `GET /api/schema/response`
- `GET /api/health`

## Request Contract

The request payload is validated with Pydantic before analysis starts.

Top-level fields:

- `data_source`
- `task`
- `parameter_fields`
- `input_parameters`
- `target_fields`
- `output_fields`
- `prediction_target_fields`
- `excluded_fields`
- `filter_parameters`
- `model_preferences`
- `response_format`
- `auto_run`

## Data Source

Example:

```json
{
  "data_source": {
    "type": "uploaded_file",
    "file_id": "pricing.csv",
    "sheet_name": "Sheet1"
  }
}
```

Notes:

- `type` currently supports only `uploaded_file`
- `file_id` must refer to a file available in the app upload store
- `sheet_name` is optional and applies to `.xlsx`

## Task Types

Supported values:

- `auto`
- `prediction`
- `classification`
- `regression`
- `similarity/search`
- `data summary/statistical analysis`

Behavior:

- `auto` lets the orchestrator choose
- explicit task values constrain the model selector

## Example Request

```json
{
  "data_source": {
    "type": "uploaded_file",
    "file_id": "pricing.csv"
  },
  "task": "auto",
  "parameter_fields": ["supplier", "category", "region", "quantity"],
  "input_parameters": {
    "supplier": "Acme",
    "category": "Transformer",
    "region": "UK",
    "quantity": 12
  },
  "target_fields": ["price"],
  "output_fields": ["supplier", "price"],
  "excluded_fields": [],
  "filter_parameters": {},
  "model_preferences": {
    "preferred_model": "auto",
    "allow_llm_to_tune": true
  },
  "response_format": "human_and_json"
}
```

## Response Contract

Success response shape:

```json
{
  "status": "success",
  "request_id": "uuid",
  "analysis_type": "linear_regression",
  "dataset_profile": {},
  "llm_plan": {},
  "model_results": {},
  "statistics": {},
  "predictions": [],
  "feature_importance": [],
  "interpretation": {
    "summary": "",
    "reasons": [],
    "caveats": [],
    "improvement_suggestions": []
  },
  "warnings": [],
  "errors": []
}
```

Error response shape:

```json
{
  "status": "error",
  "request_id": "uuid",
  "errors": [
    {
      "stage": "analysis",
      "message": "Target field(s) not found: price"
    }
  ]
}
```

## Status Codes

- `200`
  Successful analysis
- `400`
  Validation or analysis failure

## Analysis Type Values

Possible current values:

- `linear_regression`
- `random_forest_regression`
- `gradient_boosting_regression`
- `random_forest_classification`
- `gradient_boosting_classification`
- `nearest_neighbor_similarity`
- `descriptive_statistics`
- `filtered_search`

## Interpretation Block

The `interpretation` section contains:

- `summary`
- `reasons`
- `caveats`
- `improvement_suggestions`

This is intended to give downstream agents a readable summary alongside structured metrics.

## Common Error Conditions

- invalid request payload
- missing uploaded file
- missing target field
- invalid sheet name
- insufficient rows for model training
- malformed JSON in form-originated payloads

## Example Curl

```bash
curl -X POST http://127.0.0.1:5060/api/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "data_source": {"type": "uploaded_file", "file_id": "pricing.csv"},
    "task": "auto",
    "parameter_fields": ["supplier", "category", "region", "quantity"],
    "input_parameters": {"supplier": "Acme", "category": "Transformer", "region": "UK", "quantity": 12},
    "target_fields": ["price"],
    "output_fields": ["supplier", "price"],
    "excluded_fields": [],
    "model_preferences": {"preferred_model": "auto", "allow_llm_to_tune": true},
    "response_format": "human_and_json"
  }'
```

## Schema Discovery

Use these endpoints when integrating another agent or service:

- `GET /api/schema/request`
- `GET /api/schema/response`

They reflect the Pydantic model definitions used by the application.
