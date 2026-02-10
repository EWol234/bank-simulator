"""Schemas and API routes."""

from datetime import datetime

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict

from app.database import (
    Account,
    BalanceEntry,
    SimulationMetadata,
    create_simulation,
    delete_simulation,
    get_session,
    list_simulations,
    simulation_exists,
)
from app.simulation import ManualEntry, SimulationRunner

# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------


class SimulationCreate(BaseModel):
    name: str
    start_date: str | None = None
    end_date: str | None = None


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


class MetadataUpdate(BaseModel):
    start_date: str | None = None
    end_date: str | None = None


class BalanceEntryCreate(BaseModel):
    amount: float
    currency: str
    description: str | None = None
    effective_time: str


class BalanceEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    amount: float
    currency: str
    description: str | None
    effective_time: datetime


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
    create_simulation(body.name, start_date=body.start_date, end_date=body.end_date)
    return jsonify({"name": body.name, "message": "created"}), 201


@bp.route("/simulations/<sim_name>", methods=["DELETE"])
def delete_simulation_route(sim_name: str):
    if not simulation_exists(sim_name):
        return jsonify({"error": "not found"}), 404
    delete_simulation(sim_name)
    return jsonify({"name": sim_name, "message": "deleted"})


# ------------------------------------------------------------------
# Simulation metadata
# ------------------------------------------------------------------


@bp.route("/simulations/<sim_name>/metadata", methods=["GET"])
def get_metadata(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        meta = session.query(SimulationMetadata).first()
        if not meta:
            return jsonify({"start_date": None, "end_date": None})
        return jsonify({
            "start_date": meta.start_datetime.isoformat(),
            "end_date": meta.end_datetime.isoformat(),
        })


@bp.route("/simulations/<sim_name>/metadata", methods=["PATCH"])
def update_metadata(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    body = MetadataUpdate.model_validate(request.get_json())
    with get_session(sim_name) as session:
        meta = session.query(SimulationMetadata).first()
        if not meta:
            meta = SimulationMetadata(
                start_datetime=datetime.fromisoformat(body.start_date) if body.start_date else datetime.utcnow(),
                end_datetime=datetime.fromisoformat(body.end_date) if body.end_date else datetime.utcnow(),
            )
            session.add(meta)
        else:
            if body.start_date is not None:
                meta.start_datetime = datetime.fromisoformat(body.start_date)
            if body.end_date is not None:
                meta.end_datetime = datetime.fromisoformat(body.end_date)
        session.flush()
        return jsonify({
            "start_date": meta.start_datetime.isoformat(),
            "end_date": meta.end_datetime.isoformat(),
        })


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


# ------------------------------------------------------------------
# Balance entries
# ------------------------------------------------------------------


@bp.route("/simulations/<sim_name>/accounts/<int:account_id>/entries", methods=["GET"])
def list_entries(sim_name: str, account_id: int):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404
        entries = (
            session.query(BalanceEntry)
            .filter_by(account_id=account_id)
            .order_by(BalanceEntry.effective_time, BalanceEntry.id)
            .all()
        )
        return jsonify([BalanceEntryOut.model_validate(e).model_dump(mode="json") for e in entries])


@bp.route("/simulations/<sim_name>/accounts/<int:account_id>/entries", methods=["POST"])
def create_entry(sim_name: str, account_id: int):
    err = _ensure_sim(sim_name)
    if err:
        return err
    body = BalanceEntryCreate.model_validate(request.get_json())
    with get_session(sim_name) as session:
        acct = session.get(Account, account_id)
        if not acct:
            return jsonify({"error": "account not found"}), 404

        # Get simulation metadata for the runner
        meta = session.query(SimulationMetadata).first()
        start_dt = meta.start_datetime if meta else datetime.utcnow()
        end_dt = meta.end_datetime if meta else datetime.utcnow()

        propagator = ManualEntry(
            account_id=account_id,
            amount=body.amount,
            currency=body.currency,
            timestamp=datetime.fromisoformat(body.effective_time),
            description=body.description or "Manual entry",
        )

        runner = SimulationRunner(start_dt, end_dt)
        runner.add_propagator(propagator)
        runner.simulate(session)

        # Return updated entry list
        entries = (
            session.query(BalanceEntry)
            .filter_by(account_id=account_id)
            .order_by(BalanceEntry.effective_time, BalanceEntry.id)
            .all()
        )
        return jsonify([BalanceEntryOut.model_validate(e).model_dump(mode="json") for e in entries]), 201
