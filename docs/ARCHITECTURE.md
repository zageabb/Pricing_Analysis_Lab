# Architecture

## High-Level Design

Pricing Analysis Lab is structured around a Flask application with clear separation between:

- routes
- services
- deterministic analysis functions
- persistence models
- schemas
- templates and static assets

Core design goal:

- the analysis engine must work independently of the UI

This is why the JSON API, orchestrator, validation, and function registry are implemented outside the page templates and route rendering layer.

## Application Bootstrap

Entry flow:

1. [app.py](/Users/geraldabbot/Documents/Price Estimator Design/app.py) imports `create_app`
2. [pricing_analysis_lab/factory.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/factory.py) builds the Flask app
3. Config values are loaded from [pricing_analysis_lab/config.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/config.py)
4. SQLAlchemy is initialized via [pricing_analysis_lab/extensions.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/extensions.py)
5. Tables are created
6. Default settings and prompts are seeded
7. Blueprints are registered

## Main Layers

### Routes

Located in [pricing_analysis_lab/routes](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/routes).

Responsibilities:

- receive HTTP requests
- collect form or JSON input
- call service-layer functions
- render templates or return JSON

Important route modules:

- `analysis.py`
  Main wizard page, upload flow, plan preview, save/load config, and run actions
- `api.py`
  Health check, schema exposure, and `/api/analyse`
- `settings.py`
  LLM settings page
- `admin.py`
  Prompt management page
- `history.py`
  Run history page
- `workflow.py`
  Workflow documentation surface
- `json_api.py`
  Browser view of request and response schemas

### Services

Located in [pricing_analysis_lab/services](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services).

Responsibilities:

- upload and data source resolution
- spreadsheet parsing
- profiling
- request validation
- analysis orchestration
- run-history persistence
- prompt and settings persistence
- wizard session state

Important service modules:

- `spreadsheet_loader.py`
  Loads `csv` and `xlsx`
- `dataset_profiler.py`
  Builds column-level metadata
- `request_validator.py`
  Pydantic request validation
- `analysis_service.py`
  End-to-end analysis pipeline
- `analysis_runner.py`
  Executes a chosen deterministic function
- `orchestrator.py`
  Selects an analysis function and writes interpretation text
- `plan_service.py`
  Builds plan previews for the UI
- `wizard_state.py`
  Stores session-backed wizard state
- `saved_config_service.py`
  Persists reusable analysis configurations
- `settings_store.py`
  Persists LLM settings
- `prompt_store.py`
  Persists prompt metadata and prompt file content
- `llm_provider.py`
  Provider abstraction for Ollama/OpenAI-compatible endpoints

### Analysis Functions

Located in [pricing_analysis_lab/analysis](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/analysis).

Responsibilities:

- validate model-specific input assumptions
- run deterministic analysis logic
- return structured results

Registered via [pricing_analysis_lab/analysis/registry.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/analysis/registry.py).

Implemented function families:

- `random_forest.py`
- `linear_models.py`
- `gradient_boosting.py`
- `similarity.py`
- `statistics.py`
- `search.py`

Shared helpers:

- `base.py`
  Base interface and `AnalysisContext`
- `common.py`
  Shared dataset and field helpers
- `supervised.py`
  Shared supervised modeling pipeline construction

## Request Lifecycle

### UI Lifecycle

1. User uploads spreadsheet
2. Uploaded file metadata is stored
3. Wizard state is updated in session
4. Dataset is profiled for preview
5. User edits fields and parameters
6. Plan preview is generated
7. User runs analysis
8. Result is persisted to run history
9. Result JSON is shown in the UI

### API Lifecycle

1. Client calls `/api/analyse`
2. Payload is validated against Pydantic schema
3. Data source is resolved
4. Spreadsheet is loaded and profiled
5. Request is validated against actual dataset columns
6. Orchestrator selects an analysis plan
7. Analysis runner executes the registered function
8. Interpretation block is generated
9. Run history is written
10. JSON response is returned

## Persistence Model

Defined in [pricing_analysis_lab/models.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/models.py).

Tables:

- `AppSetting`
  Stores LLM settings
- `PromptTemplate`
  Tracks prompt file metadata
- `UploadedDataset`
  Tracks uploaded file metadata
- `AnalysisRun`
  Stores request/response history
- `SavedAnalysisConfig`
  Stores reusable wizard configurations

Storage characteristics:

- SQLite by default
- file-backed local persistence
- suitable for local/single-user workflows

## Orchestration Strategy

The orchestrator in [pricing_analysis_lab/services/orchestrator.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services/orchestrator.py) currently uses deterministic heuristics rather than a live multi-call LLM pipeline.

Decision inputs include:

- requested task
- preferred model
- target field type
- dataset row count
- whether input parameters are present

Typical routing behavior:

- small numeric dataset
  `linear_regression`
- medium numeric dataset
  `random_forest_regression`
- larger numeric dataset
  `gradient_boosting_regression`
- categorical target
  random forest or gradient boosting classification
- search request with input parameters
  `nearest_neighbor_similarity`
- no predictive setup
  `descriptive_statistics` or `filtered_search`

## LLM Integration Status

The app includes:

- editable prompt files
- persisted provider settings
- provider adapters for Ollama and OpenAI-compatible APIs

Current reality:

- the provider abstraction is present
- the core orchestration path is still heuristic-first
- no free-text LLM-generated executable code is run

This keeps analysis deterministic and testable.

## Frontend Structure

Templates:

- [pricing_analysis_lab/templates/base.html](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/templates/base.html)
- [pricing_analysis_lab/templates/analysis/home.html](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/templates/analysis/home.html)
- settings, prompt, workflow, history, and JSON API pages

Styling:

- [pricing_analysis_lab/static/app.css](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/static/app.css)

The frontend is intentionally lightweight and server-rendered.

## Test Coverage Areas

The test suite covers:

- app bootstrap
- spreadsheet loading
- dataset profiling
- request validation
- settings and prompts
- analysis registry behavior
- orchestrator decisions
- saved configs
- API success and error flows

Tests live in [tests](/Users/geraldabbot/Documents/Price Estimator Design/tests).
