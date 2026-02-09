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

    return application
