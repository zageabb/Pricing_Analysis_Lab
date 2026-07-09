# Pricing Analysis Lab

Pricing Analysis Lab is a local Flask application for spreadsheet-driven pricing analysis. It is designed for two kinds of use:

- human-guided analysis through a multi-step browser wizard
- machine or agent-driven analysis through a JSON API

The application profiles uploaded pricing datasets, builds an analysis plan, runs deterministic statistical or machine-learning functions, and returns both structured JSON and human-readable interpretation.

## Documentation Map

- [docs/USER_GUIDE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/USER_GUIDE.md)
  User-facing walkthrough of the wizard, uploads, saved configs, settings, prompts, and results
- [docs/API_REFERENCE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/API_REFERENCE.md)
  JSON request and response behavior for `/api/analyse` and related schema endpoints
- [docs/ARCHITECTURE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/ARCHITECTURE.md)
  Internal design of routes, services, analysis functions, persistence, and orchestration
- [docs/OPERATIONS.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/OPERATIONS.md)
  Setup, runtime configuration, local operations, troubleshooting, and maintenance
- [docs/DEVELOPER_GUIDE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/DEVELOPER_GUIDE.md)
  How to extend the app with new models, routes, prompts, tests, and workflows

## Core Capabilities

- Upload `CSV` and `XLSX` datasets
- Inspect column profile, preview rows, detected types, null counts, and example values
- Work through a multi-step analysis wizard
- Save and reload reusable analysis configurations
- Configure prompt templates and LLM settings from the UI
- Accept analysis requests via `POST /api/analyse`
- Auto-select an analysis function when `task` or `preferred_model` is set to `auto`
- Persist run history, prompt metadata, settings, upload metadata, and saved analysis configs in SQLite

## Implemented Analysis Functions

- `random_forest_regression`
- `random_forest_classification`
- `linear_regression`
- `gradient_boosting_regression`
- `gradient_boosting_classification`
- `nearest_neighbor_similarity`
- `descriptive_statistics`
- `filtered_search`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

Open [http://127.0.0.1:5060](http://127.0.0.1:5060).

## Main Pages

- `/` analysis wizard
- `/settings` LLM provider settings
- `/admin/prompts` prompt manager
- `/workflow` workflow diagram
- `/json-api` request/response schema display
- `/history` run history
- `/api/health` health endpoint

## Project Structure

- [app.py](/Users/geraldabbot/Documents/Price Estimator Design/app.py)
  Local app entry point
- [pricing_analysis_lab/factory.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/factory.py)
  Flask app factory and blueprint registration
- [pricing_analysis_lab/routes](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/routes)
  Browser pages and API endpoints
- [pricing_analysis_lab/services](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services)
  Orchestration, uploads, persistence, profiling, and validation
- [pricing_analysis_lab/analysis](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/analysis)
  Deterministic analysis function implementations
- [pricing_analysis_lab/models.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/models.py)
  SQLite-backed persistence models
- [tests](/Users/geraldabbot/Documents/Price Estimator Design/tests)
  Automated tests

## Running Tests

```bash
python3 -m pytest -q
```

## Current Limitations

- The wizard is server-rendered and session-backed rather than a richer client-side application
- Orchestration currently uses deterministic heuristics first; live LLM decision-making is scaffolded, not deeply integrated
- Prompt storage is file-backed and simple rather than versioned
- Mermaid workflow display is documentation-oriented rather than a full embedded visual renderer

## Recommended Reading Order

If you need to understand the application quickly:

1. Read [docs/USER_GUIDE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/USER_GUIDE.md)
2. Read [docs/API_REFERENCE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/API_REFERENCE.md)
3. Read [docs/ARCHITECTURE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/ARCHITECTURE.md)
4. Use [docs/DEVELOPER_GUIDE.md](/Users/geraldabbot/Documents/Price Estimator Design/docs/DEVELOPER_GUIDE.md) when changing code
