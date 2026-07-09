from flask import Blueprint, render_template


workflow_bp = Blueprint("workflow", __name__)


WORKFLOW_MERMAID = """flowchart LR
    A["User or Agent Input"] --> B["Data Profiler"]
    B --> C["LLM Orchestrator"]
    C --> D["Model Selector"]
    D --> E["Feature Planner"]
    E --> F["Registered Function Caller"]
    F --> G["Statistical Results"]
    G --> H["LLM Result Analyser"]
    H --> I["UI Output and JSON Output"]
"""


@workflow_bp.get("/")
def index():
    return render_template("workflow/index.html", mermaid_source=WORKFLOW_MERMAID)
