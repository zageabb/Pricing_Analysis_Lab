# Developer Guide

## Development Principles

This application is organized so that:

- analysis logic is independent of the UI
- request validation is explicit and typed
- model execution is deterministic
- LLM integration is optional and bounded
- persistence is simple and local-first

When changing the app, keep those boundaries intact.

## Key Extension Points

### Add a New Analysis Function

1. Create a new module under [pricing_analysis_lab/analysis](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/analysis)
2. Implement an `AnalysisFunction`
3. Add `validate()` and `run()`
4. Register it in [pricing_analysis_lab/analysis/registry.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/analysis/registry.py)
5. Update orchestration logic in [pricing_analysis_lab/services/orchestrator.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services/orchestrator.py)
6. Add focused tests

### Add a New Page

1. Add a blueprint route under [pricing_analysis_lab/routes](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/routes)
2. Add a template under `templates/`
3. Register the blueprint in [pricing_analysis_lab/factory.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/factory.py)
4. Link it from [pricing_analysis_lab/templates/base.html](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/templates/base.html) if appropriate

### Add a New Persisted Setting

1. Add a default in [pricing_analysis_lab/services/settings_store.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services/settings_store.py)
2. Expose it in the settings form
3. Use it in the relevant service
4. Add or update tests

### Add a New Prompt

1. Add the prompt to `DEFAULT_PROMPTS` in [pricing_analysis_lab/services/prompt_store.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services/prompt_store.py)
2. Confirm it is seeded at startup
3. Update any calling service if the prompt is actually consumed

## Model Implementation Notes

Shared supervised utilities live in:

- [pricing_analysis_lab/analysis/supervised.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/analysis/supervised.py)

Use those helpers when adding:

- more regressors
- more classifiers
- shared preprocessing or feature engineering logic

This keeps pipeline construction consistent across models.

## Request and Response Schema Changes

Schemas live in [pricing_analysis_lab/schemas.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/schemas.py).

If you change schema behavior:

1. update the Pydantic model
2. update affected services or routes
3. update `/api/schema/*` expectations if needed
4. update documentation
5. add or update tests

## Wizard Changes

Wizard session behavior lives in [pricing_analysis_lab/services/wizard_state.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services/wizard_state.py).

If you add a new wizard field:

1. add it to the default wizard state
2. update form parsing
3. update hidden carry-forward fields in the analysis template
4. update saved config behavior if the field should persist

## Run History Changes

Run-history persistence is centered on:

- [pricing_analysis_lab/models.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/models.py)
- [pricing_analysis_lab/services/run_history.py](/Users/geraldabbot/Documents/Price Estimator Design/pricing_analysis_lab/services/run_history.py)

If you add result metadata worth tracking, prefer storing it inside the persisted response JSON unless a first-class queryable column is truly needed.

## Test Strategy

Add tests near the behavior you changed:

- loader or parser change
  add to spreadsheet loader tests
- orchestration change
  add to orchestrator tests
- model change
  add to analysis registry tests
- route/API change
  add to API tests
- persistence change
  add focused service tests

Run:

```bash
python3 -m pytest -q
```

## Documentation Practice

Whenever the app changes meaningfully:

- update [README.md](/Users/geraldabbot/Documents/Price Estimator Design/README.md)
- update the relevant `docs/*.md` file
- keep user-facing docs and architecture docs aligned

This project now has separate docs so changes can be documented at the right level instead of forcing everything into one README.
