from __future__ import annotations

from typing import Any

from ..schemas import AnalysisPlan


def resolve_effective_plan(base_plan: dict[str, Any], manual_plan: dict[str, Any] | None) -> AnalysisPlan:
    if not isinstance(manual_plan, dict) or not manual_plan:
        return AnalysisPlan.model_validate(base_plan)
    plan = dict(base_plan)
    for key in ("selected_function", "reason", "target_field"):
        value = manual_plan.get(key)
        if isinstance(value, str) and value.strip():
            plan[key] = value.strip()
        elif key == "target_field" and value is None:
            plan[key] = None
    if isinstance(manual_plan.get("feature_fields"), list) and manual_plan["feature_fields"]:
        plan["feature_fields"] = [str(item).strip() for item in manual_plan["feature_fields"] if str(item).strip()]
    for key in ("model_settings", "preprocessing", "validation"):
        value = manual_plan.get(key)
        if isinstance(value, dict) and value:
            plan[key] = value
    return AnalysisPlan.model_validate(plan)
