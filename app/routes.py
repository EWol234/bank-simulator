"""Schemas and API routes."""

from datetime import datetime

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict

from app.database import (
    Account,
    create_simulation,
    delete_simulation,
    get_session,
    list_simulations,
    simulation_exists,
)

# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------


class SimulationCreate(BaseModel):
    name: str


class SimulationList(BaseModel):
    simulations: list[str]


class AccountCreate(BaseModel):
    name: str


class AccountUpdate(BaseModel):
    name: str | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


# ------------------------------------------------------------------
# Blueprint
# ------------------------------------------------------------------

bp = Blueprint("api", __name__)


def _ensure_sim(sim_name: str):
    if not simulation_exists(sim_name):
        return jsonify({"error": f"Simulation '{sim_name}' not found"}), 404
    return None


# ------------------------------------------------------------------
# Simulation management
# ------------------------------------------------------------------


@bp.route("/simulations", methods=["GET"])
def list_simulations_route():
    names = list_simulations()
    return jsonify(SimulationList(simulations=names).model_dump())


@bp.route("/simulations", methods=["POST"])
def create_simulation_route():
    body = SimulationCreate.model_validate(request.get_json())
    if simulation_exists(body.name):
        return jsonify({"error": f"Simulation '{body.name}' already exists"}), 409
    create_simulation(body.name)
    return jsonify({"name": body.name, "message": "created"}), 201


@bp.route("/simulations/<sim_name>", methods=["DELETE"])
def delete_simulation_route(sim_name: str):
    if not simulation_exists(sim_name):
        return jsonify({"error": "not found"}), 404
    delete_simulation(sim_name)
    return jsonify({"name": sim_name, "message": "deleted"})


# ------------------------------------------------------------------
# Accounts
# ------------------------------------------------------------------


@bp.route("/simulations/<sim_name>/accounts", methods=["GET"])
def list_accounts(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        rows = session.query(Account).order_by(Account.id).all()
        return jsonify([AccountOut.model_validate(r).model_dump(mode="json") for r in rows])


@bp.route("/simulations/<sim_name>/accounts", methods=["POST"])
def create_account(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    body = AccountCreate.model_validate(request.get_json())
    with get_session(sim_name) as session:
        acct = Account(name=body.name)
        session.add(acct)
        session.flush()
        out = AccountOut.model_validate(acct).model_dump(mode="json")
    return jsonify(out), 201


@bp.route("/simulations/<sim_name>/accounts/<int:account_id>", methods=["GET"])
def get_account(sim_name: str, account_id: int):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        return jsonify(AccountOut.model_validate(acct).model_dump(mode="json"))


@bp.route("/simulations/<sim_name>/accounts/<int:account_id>", methods=["PATCH"])
def update_account(sim_name: str, account_id: int):
    err = _ensure_sim(sim_name)
    if err:
        return err
    body = AccountUpdate.model_validate(request.get_json())
    with get_session(sim_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        if body.name is not None:
            acct.name = body.name
        session.flush()
        return jsonify(AccountOut.model_validate(acct).model_dump(mode="json"))


@bp.route("/simulations/<sim_name>/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(sim_name: str, account_id: int):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        session.delete(acct)
    return jsonify({"message": "deleted"})
