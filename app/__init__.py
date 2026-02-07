"""Flask application factory."""

from flask import Flask, jsonify
from pydantic import ValidationError

from app.config import Config
from app.database import DatabaseManager


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__)

    if config is None:
        config = Config()

    # Attach the database manager so routes can access it
    app.config["DB_MANAGER"] = DatabaseManager(config.DATA_DIR)

    # Register blueprints
    from app.routes.databases import bp as databases_bp
    from app.routes.accounts import bp as accounts_bp

    app.register_blueprint(databases_bp)
    app.register_blueprint(accounts_bp)

    # Global Pydantic validation error handler
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({"error": "validation_error", "details": exc.errors()}), 422

    return app
