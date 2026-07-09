from __future__ import annotations

import json
from uuid import uuid4

from ..extensions import db
from ..models import AnalysisRun


def create_run(request_json: dict) -> AnalysisRun:
    run = AnalysisRun(
        request_id=str(uuid4()),
        status="pending",
        request_json=json.dumps(request_json),
    )
    db.session.add(run)
    db.session.commit()
    return run


def complete_run(run: AnalysisRun, status: str, analysis_type: str | None, response_json: dict) -> AnalysisRun:
    run.status = status
    run.analysis_type = analysis_type
    run.response_json = json.dumps(response_json)
    db.session.add(run)
    db.session.commit()
    return run
