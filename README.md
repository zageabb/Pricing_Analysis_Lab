# Pricing Analysis Lab

Pricing Analysis Lab is a local Flask application for spreadsheet-driven pricing analysis. It supports both human-guided UI use and agent-style JSON calls, with deterministic analysis functions behind an orchestration layer.

## What It Does

- Upload and inspect `CSV` and `XLSX` pricing datasets
- Profile columns for type, null count, unique count, and example values
- Accept structured analysis requests through the UI or `POST /api/analyse`
- Auto-select an analysis plan
- Run deterministic analysis functions from a safe registry
- Return human-readable interpretation plus structured JSON output
- Persist prompts, LLM settings, uploaded dataset metadata, and run history in SQLite

## Current Implemented Functions

- `random_forest_regression`
- `random_forest_classification`
- `descriptive_statistics`
- `filtered_search`

The Random Forest pipeline uses `scikit-learn` with `ColumnTransformer`, numeric/categorical preprocessing, imputation, train/test split, metrics, predictions, and feature importance output.

## Project Structure

- `app.py` - local Flask entry point
- `pricing_analysis_lab/config.py` - runtime configuration
- `pricing_analysis_lab/models.py` - SQLite-backed persistence models
- `pricing_analysis_lab/routes/` - UI pages and API routes
- `pricing_analysis_lab/services/` - upload, validation, orchestration, persistence, and analysis services
- `pricing_analysis_lab/analysis/` - registered deterministic analysis functions
- `tests/` - loader, validation, settings, API, and model tests

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

Open [http://127.0.0.1:5060](http://127.0.0.1:5060).

## Environment Variables

- `SECRET_KEY`
- `DATABASE_URL`
- `DATA_DIR`
- `UPLOAD_DIR`
- `PROMPT_DIR`
- `HOST`
- `PORT`
- `FLASK_DEBUG`

## LLM Configuration

Use the `LLM Settings` page to configure:

- provider
- base URL
- API key environment variable name
- model name
- temperature
- top_p
- max tokens
- timeout
- retry count
- streaming
- JSON mode

Current provider adapter support:

- `ollama`
- `openai`
- `azure_openai`
- `openai_compatible`
- fallback `dummy`

## Uploading a Spreadsheet

1. Open the `Analysis` page.
2. Upload a `.csv` or `.xlsx` file.
3. Review the detected profile and preview.
4. Enter target fields, parameter fields, and input parameters.
5. Run analysis and inspect the JSON result block.

## API Usage

Endpoint:

```bash
POST /api/analyse
```

Example request:

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
  "model_preferences": {
    "preferred_model": "auto",
    "allow_llm_to_tune": true
  },
  "response_format": "human_and_json"
}
```

Example success response:

```json
{
  "status": "success",
  "request_id": "uuid",
  "analysis_type": "random_forest_regression",
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

Example error response:

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

## Tests

Run:

```bash
python3 -m pytest -q
```

Current coverage includes:

- CSV loading
- XLSX loading
- column profiling
- JSON request validation
- prompt loading
- settings loading
- Random Forest regression
- Random Forest classification
- descriptive statistics fallback
- invalid target field handling
- insufficient row handling
- JSON API success and error paths

## Adding New Analysis Functions

1. Add a new function under `pricing_analysis_lab/analysis/`.
2. Implement `validate()` and `run()`.
3. Register it in `pricing_analysis_lab/analysis/registry.py`.
4. Update orchestration rules in `pricing_analysis_lab/services/orchestrator.py`.
5. Add focused tests.

## Known Limitations

- The main UI is functional but still compact; it is not yet a fully split multi-page wizard.
- Prompt editing is file-backed and simple rather than versioned.
- LLM-assisted planning currently uses deterministic heuristics first; provider-backed prompt execution is scaffolded but not yet deeply integrated into orchestration decisions.
- Mermaid workflow is currently displayed as source text rather than a bundled offline renderer.

## Next Recommended Improvements

- Add true multi-step UI state with editable generated plans before execution
- Add upload history and saved analysis configurations
- Add cross-validation controls and richer warnings
- Extend the provider abstraction with live orchestrator/result-interpretation calls
- Add similarity ranking and additional regression/classification models
