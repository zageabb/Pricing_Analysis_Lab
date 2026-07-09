# Operations Guide

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

Default bind address:

```text
0.0.0.0:5052
```

Open locally with:

```text
http://127.0.0.1:5052
```

Open from another device on the same network with:

```text
http://<your-machine-ip>:5052
```

## Runtime Configuration

Defined primarily in [pricing_analysis_lab/config.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/config.py).

Environment variables:

- `SECRET_KEY`
- `DATABASE_URL`
- `DATA_DIR`
- `UPLOAD_DIR`
- `PROMPT_DIR`
- `HOST`
- `PORT`
- `FLASK_DEBUG`

## Storage Locations

Default runtime storage:

- SQLite DB in the project root unless overridden by `DATABASE_URL`
- uploaded files in the configured upload directory
- prompt files in the configured prompt directory
- session state in Flask session cookies

## Starting the App

```bash
python3 app.py
```

What happens on startup:

- directories are created if missing
- SQLAlchemy initializes
- tables are created
- default settings are seeded
- default prompt files are seeded
- blueprints are registered

## Running Tests

```bash
python3 -m pytest -q
```

Current expected result:

- passing suite
- one environment-specific warning may appear from `joblib` in similarity tests on some machines

## Updating LLM Settings

Use `/settings` to change:

- provider
- base URL
- model
- timeout
- token and sampling settings

These values are persisted in SQLite via `AppSetting`.

## Updating Prompts

Use `/admin/prompts`.

Current behavior:

- prompt content is stored in files
- prompt metadata is tracked in `PromptTemplate`
- edits take effect immediately for future reads

## Upload Management

Uploaded datasets are:

- stored on disk
- tracked in `UploadedDataset`

If storage cleanup is needed:

- remove unwanted uploaded files from the upload directory
- remove corresponding rows from the database if you want metadata cleanup too

## Database Notes

The app uses SQLite by default and is optimized for local operation.

Suitable for:

- local development
- single-user workflows
- small team demonstrations

Not yet designed for:

- concurrent multi-user production workloads
- complex background job processing

## Troubleshooting

### App starts but analysis fails

Check:

- uploaded file exists
- target field is valid
- dataset has enough rows
- JSON fields are valid

### Spreadsheet upload works but plan generation fails

Check:

- target field spelling
- selected sheet name
- whether the task type matches the target field type

### Prompt or settings edits do not appear

Check:

- browser cache or stale page state
- database file permissions
- prompt directory write permissions

### API calls return `400`

Check:

- payload shape
- missing required fields
- invalid data source references
- unsupported task/target combinations

## Maintenance Suggestions

- back up the SQLite database periodically if run history matters
- back up prompt files if prompt tuning matters
- prune uploaded files if the upload directory grows too large
- keep requirements current and rerun the test suite after upgrades
