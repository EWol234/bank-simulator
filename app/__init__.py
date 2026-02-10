"""Flask application factory."""

import os

from flask import Flask, jsonify
from pydantic import ValidationError

import app.database as database


def create_app(data_dir: str | None = None) -> Flask:
    application = Flask(__name__)

    database.DATA_DIR = os.path.abspath(
        data_dir
        or os.environ.get("BANK_SIM_DATA_DIR")
        or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    )
    os.makedirs(database.DATA_DIR, exist_ok=True)

    from app.routes import bp

    application.register_blueprint(bp)

    @application.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({"error": "validation_error", "details": exc.errors()}), 422

    @application.before_request
    def handle_options():
        from flask import request
        if request.method == "OPTIONS":
            from flask import make_response
            resp = make_response("", 204)
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return resp

    @application.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    return application
