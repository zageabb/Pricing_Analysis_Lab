from flask import Blueprint, render_template

from ..schemas import request_schema, response_schema


json_api_bp = Blueprint("json_api", __name__)


@json_api_bp.get("/")
def index():
    return render_template(
        "json_api/index.html",
        request_schema=request_schema(),
        response_schema=response_schema(),
    )
