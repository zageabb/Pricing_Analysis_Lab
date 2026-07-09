# User Guide

## Purpose

Pricing Analysis Lab helps users analyze spreadsheet pricing data through a guided workflow. The application can:

- summarize a dataset
- find similar rows
- predict numeric values
- predict categorical values

It works best when the dataset has consistent columns, a usable target field for prediction tasks, and enough rows for model training.

## Main Workflow

The application is organized around a seven-step wizard:

1. Select spreadsheet
2. Choose fields
3. Enter parameters
4. Generate model plan
5. Review plan
6. Run analysis
7. Inspect results

The current implementation renders these steps on one page, but the state is stored as a wizard session and follows this staged workflow.

## Step 1: Upload a Spreadsheet

Supported formats:

- `.csv`
- `.xlsx`

What happens after upload:

- the file is stored in the configured upload directory
- upload metadata is persisted in SQLite
- the selected file becomes the current wizard data source
- the app profiles the spreadsheet and shows a preview

## Step 2: Choose Fields

Important field groups:

- `parameter_fields`
  Fields that can be used as model inputs
- `target_fields`
  Fields the model should predict or classify
- `output_fields`
  Fields shown back in search or similarity results
- `excluded_fields`
  Fields that should not be used as features

General guidance:

- For prediction or regression, set one numeric target field such as `price`
- For classification, set one categorical target field such as `price_band`
- For similarity/search, parameter fields should describe the rows you want to compare

## Step 3: Enter Parameters

Two JSON blocks are supported:

- `input_parameters`
  A single target request or input example, such as a proposed item you want priced
- `filter_parameters`
  Hard filters to limit the dataset before analysis

Example `input_parameters`:

```json
{
  "supplier": "Acme",
  "category": "Transformer",
  "region": "UK",
  "quantity": 12
}
```

Example `filter_parameters`:

```json
{
  "region": "UK"
}
```

## Step 4: Generate Model Plan

When you generate a plan, the application:

- validates the request
- loads the selected dataset
- profiles the dataset
- chooses an analysis function using the orchestrator
- builds a plan preview

The plan preview includes:

- selected function
- reason for the choice
- target field
- feature fields
- model settings
- validation settings

## Step 5: Review Plan

The plan preview is the application’s explanation of how it intends to solve the request.

Typical outcomes:

- `linear_regression`
  Chosen for smaller numeric datasets or when a simpler baseline is appropriate
- `random_forest_regression`
  Chosen for medium-sized numeric prediction tasks
- `gradient_boosting_regression`
  Chosen for larger numeric datasets where a stronger tree-based regressor may help
- `random_forest_classification`
  Chosen for categorical targets
- `gradient_boosting_classification`
  Chosen for larger categorical prediction tasks
- `nearest_neighbor_similarity`
  Chosen for search or similarity requests with input parameters
- `descriptive_statistics`
  Chosen when prediction is not appropriate
- `filtered_search`
  Chosen when exact or near-exact filtering is safer than modeling

## Step 6: Run Analysis

When you run analysis, the application:

- validates the request against the dataset
- executes the chosen deterministic function
- captures structured metrics
- produces a final JSON response
- stores the run in history

No arbitrary LLM-generated code is executed during analysis.

## Step 7: Inspect Results

Result sections usually include:

- `analysis_type`
- `dataset_profile`
- `llm_plan`
- `model_results`
- `statistics`
- `predictions`
- `feature_importance`
- `interpretation`
- `warnings`
- `errors`

Interpretation is currently produced by deterministic app logic rather than a deeply integrated live LLM reasoning pass.

## Saved Analysis Configurations

You can save the current wizard state as a reusable configuration.

What a saved config contains:

- current data source reference
- task type
- parameter fields
- target fields
- output fields
- excluded fields
- input parameters
- filter parameters
- model preferences

Use cases:

- recurring supplier comparisons
- repeated pricing requests by region
- reusable baseline setups for different product categories

## LLM Settings Page

The LLM settings page stores provider-related configuration, including:

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

These settings are persisted in SQLite and are intended for future deeper orchestration integration as well as current provider abstraction support.

## Prompt Manager

Prompt templates are editable from the prompt manager. The current app keeps them as local files and tracks their metadata in the database.

This is useful when:

- you want to refine orchestration guidance
- you want to adjust result interpretation wording
- you want to experiment with future LLM-driven planning

## Run History

Each analysis run stores:

- a generated request ID
- run status
- selected analysis type
- input request JSON
- output response JSON
- timestamp

Use run history for:

- auditing what was run
- reproducing a previous request
- comparing outputs across different settings

## Tips for Better Results

- Use clear target fields with low missingness
- Exclude noisy identifiers that do not help prediction
- Prefer more rows for tree-based models
- Use similarity mode when you want analogous rows instead of a learned prediction
- Treat very small datasets as directional rather than definitive

## Common Failure Cases

- Target field does not exist
- Too few rows for the chosen model
- Uploaded file not found
- Invalid JSON in input or filter parameters
- Wrong sheet name for `.xlsx`

When these happen, check the returned `errors` block or the flashed message in the UI.
