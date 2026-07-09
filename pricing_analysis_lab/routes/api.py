from flask import Blueprint, jsonify, request

from ..schemas import request_schema, response_schema
from ..services.analysis_service import analyse_payload


api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "app": "Pricing_Analysis_Lab"})


@api_bp.get("/schema/request")
def request_schema_view():
    return jsonify(request_schema())


@api_bp.get("/schema/response")
def response_schema_view():
    return jsonify(response_schema())


@api_bp.post("/analyse")
def analyse():
    payload = request.get_json(silent=True) or {}
    response = analyse_payload(payload)
    status_code = 200 if response["status"] == "success" else 400
    return jsonify(response), status_code
