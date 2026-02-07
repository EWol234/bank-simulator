"""Routes for managing database files (create / list / delete)."""

from flask import Blueprint, current_app, jsonify, request

from app.schemas import DatabaseCreate, DatabaseList

bp = Blueprint("databases", __name__, url_prefix="/databases")


def _db_manager():
    return current_app.config["DB_MANAGER"]


@bp.route("", methods=["GET"])
def list_databases():
    names = _db_manager().list_databases()
    return jsonify(DatabaseList(databases=names).model_dump())


@bp.route("", methods=["POST"])
def create_database():
    body = DatabaseCreate.model_validate(request.get_json())
    mgr = _db_manager()
    if mgr.database_exists(body.name):
        return jsonify({"error": f"Database '{body.name}' already exists"}), 409
    mgr.create_database(body.name)
    return jsonify({"name": body.name, "message": "created"}), 201


@bp.route("/<db_name>", methods=["DELETE"])
def delete_database(db_name: str):
    mgr = _db_manager()
    if not mgr.database_exists(db_name):
        return jsonify({"error": "not found"}), 404
    mgr.delete_database(db_name)
    return jsonify({"name": db_name, "message": "deleted"})
