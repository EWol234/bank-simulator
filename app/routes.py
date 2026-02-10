"""Schemas and API routes."""

from datetime import datetime

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict

from app.database import (
    Account,
    FundingRule,
    BalanceEntry,
    SimulationMetadata,
    create_simulation,
    delete_simulation,
    ensure_tables,
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


class FundingRuleCreate(BaseModel):
    rule_type: str
    target_account_id: int
    source_account_id: int
    time_of_day: str
    currency: str = "USD"
    threshold: float = 0.0
    target_amount: float = 0.0


class FundingRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_type: str
    target_account_id: int
    source_account_id: int
    time_of_day: str
    currency: str
    threshold: float
    target_amount: float


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
# Funding rules
# ------------------------------------------------------------------


@bp.route("/simulations/<sim_name>/funding-rules", methods=["GET"])
def list_funding_rules(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    ensure_tables(sim_name)
    with get_session(sim_name) as session:
        rows = session.query(FundingRule).order_by(FundingRule.id).all()
        return jsonify([FundingRuleOut.model_validate(r).model_dump(mode="json") for r in rows])


@bp.route("/simulations/<sim_name>/funding-rules", methods=["POST"])
def create_funding_rule(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    body = FundingRuleCreate.model_validate(request.get_json())

    # Validate time format
    try:
        datetime.strptime(body.time_of_day, "%H:%M:%S")
    except ValueError:
        return jsonify({"error": "time_of_day must be in HH:MM:SS format"}), 422

    if body.rule_type not in ("BACKUP_FUNDING", "TOPUP", "SWEEP_OUT"):
        return jsonify({"error": "rule_type must be BACKUP_FUNDING, TOPUP, or SWEEP_OUT"}), 422

    if body.target_account_id == body.source_account_id:
        return jsonify({"error": "Target and source accounts must be different"}), 422

    if body.rule_type == "BACKUP_FUNDING":
        body.threshold = 0.0
        body.target_amount = 0.0
    elif body.rule_type == "TOPUP":
        if body.target_amount < body.threshold:
            return jsonify({"error": "target_amount must be >= threshold"}), 422
    elif body.rule_type == "SWEEP_OUT":
        if body.target_amount > body.threshold:
            return jsonify({"error": "For SWEEP_OUT, target_amount (balance to leave) must be <= threshold (trigger level)"}), 422

    ensure_tables(sim_name)
    with get_session(sim_name) as session:
        # Validate accounts exist
        if not session.get(Account, body.target_account_id):
            return jsonify({"error": "Target account not found"}), 404
        if not session.get(Account, body.source_account_id):
            return jsonify({"error": "Source account not found"}), 404

        rule = FundingRule(
            rule_type=body.rule_type,
            target_account_id=body.target_account_id,
            source_account_id=body.source_account_id,
            time_of_day=body.time_of_day,
            currency=body.currency,
            threshold=body.threshold,
            target_amount=body.target_amount,
        )
        session.add(rule)
        session.flush()

        # Run simulation with all backup funding rules
        meta = session.query(SimulationMetadata).first()
        if meta:
            runner = SimulationRunner(meta.start_datetime, meta.end_datetime, session)
            runner.simulate(session)

        return jsonify(FundingRuleOut.model_validate(rule).model_dump(mode="json")), 201


@bp.route("/simulations/<sim_name>/funding-rules/<int:rule_id>", methods=["DELETE"])
def delete_funding_rule(sim_name: str, rule_id: int):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        rule = session.get(FundingRule, rule_id)
        if not rule:
            return jsonify({"error": "Funding rule not found"}), 404

        session.delete(rule)
        session.flush()

        # Delete balance entries generated by this rule
        session.query(BalanceEntry).filter(
            BalanceEntry.rule_id == rule_id
        ).delete(synchronize_session="fetch")
        session.flush()

        # Re-run simulation to recalculate remaining rules' effects
        meta = session.query(SimulationMetadata).first()
        if meta:
            runner = SimulationRunner(meta.start_datetime, meta.end_datetime, session)
            runner.simulate(session)

    return jsonify({"message": "deleted"})


# ------------------------------------------------------------------
# Balance entries
# ------------------------------------------------------------------


@bp.route("/simulations/<sim_name>/activity", methods=["GET"])
def list_activity(sim_name: str):
    err = _ensure_sim(sim_name)
    if err:
        return err
    with get_session(sim_name) as session:
        rows = (
            session.query(BalanceEntry, Account.name)
            .join(Account, BalanceEntry.account_id == Account.id)
            .order_by(BalanceEntry.effective_time, BalanceEntry.account_id, BalanceEntry.id)
            .all()
        )
        result = []
        for entry, account_name in rows:
            result.append({
                "id": entry.id,
                "account_id": entry.account_id,
                "account_name": account_name,
                "amount": entry.amount,
                "currency": entry.currency,
                "description": entry.description,
                "effective_time": entry.effective_time.isoformat(),
            })
        return jsonify(result)


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

        runner = SimulationRunner(start_dt, end_dt, session)
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


# ------------------------------------------------------------------
# Seed demo data
# ------------------------------------------------------------------


@bp.route("/simulations/<sim_name>/seed", methods=["POST"])
def seed_demo_data(sim_name: str):
    if simulation_exists(sim_name):
        delete_simulation(sim_name)
    create_simulation(sim_name, start_date="2025-01-06T00:00:00", end_date="2025-01-10T23:59:59")

    with get_session(sim_name) as session:
        # Create accounts
        acct_ramp = Account(name="RAMP_JPM")
        acct_citi = Account(name="CITI_JPM")
        acct_hub = Account(name="INCREASE_HUB")
        acct_saas = Account(name="INCREASE_SAAS")
        acct_reimb = Account(name="INCREASE_REIMB")
        session.add_all([acct_ramp, acct_citi, acct_hub, acct_saas, acct_reimb])
        session.flush()

        # Initial balances at 2025-01-06 00:00
        initial_time = datetime(2025, 1, 6, 0, 0, 0)
        for acct_id, amount, desc in [
            (acct_ramp.id, 500000.0, "Initial balance"),
            (acct_citi.id, 50000.0, "Initial balance"),
            (acct_hub.id, 30000.0, "Initial balance"),
            (acct_saas.id, 60000.0, "Initial balance"),
            (acct_reimb.id, 15000.0, "Initial balance"),
        ]:
            session.add(BalanceEntry(
                account_id=acct_id, amount=amount, currency="USD",
                description=desc, effective_time=initial_time,
            ))
        session.flush()

        # Funding rules
        for rd in [
            {"rule_type": "BACKUP_FUNDING", "target_account_id": acct_citi.id,
             "source_account_id": acct_ramp.id, "time_of_day": "09:00:00",
             "currency": "USD", "threshold": 0.0, "target_amount": 0.0},
            {"rule_type": "BACKUP_FUNDING", "target_account_id": acct_hub.id,
             "source_account_id": acct_ramp.id, "time_of_day": "09:00:00",
             "currency": "USD", "threshold": 0.0, "target_amount": 0.0},
            {"rule_type": "TOPUP", "target_account_id": acct_reimb.id,
             "source_account_id": acct_hub.id, "time_of_day": "10:00:00",
             "currency": "USD", "threshold": 10000.0, "target_amount": 25000.0},
            {"rule_type": "SWEEP_OUT", "target_account_id": acct_hub.id,
             "source_account_id": acct_saas.id, "time_of_day": "11:00:00",
             "currency": "USD", "threshold": 80000.0, "target_amount": 50000.0},
        ]:
            session.add(FundingRule(**rd))
        session.flush()

        # Simulated activity
        for acct_id, amount, eff_time, desc in [
            (acct_citi.id, -60000.0, datetime(2025, 1, 7, 8, 0, 0), "Wire payment - vendor"),
            (acct_reimb.id, -18000.0, datetime(2025, 1, 7, 8, 0, 0), "Reimbursement payout"),
            (acct_saas.id, 50000.0, datetime(2025, 1, 8, 7, 0, 0), "SaaS revenue deposit"),
            (acct_citi.id, -30000.0, datetime(2025, 1, 9, 8, 0, 0), "Wire payment - rent"),
            (acct_reimb.id, -20000.0, datetime(2025, 1, 9, 8, 0, 0), "Reimbursement batch"),
            (acct_saas.id, 40000.0, datetime(2025, 1, 10, 7, 0, 0), "SaaS revenue deposit"),
        ]:
            session.add(BalanceEntry(
                account_id=acct_id, amount=amount, currency="USD",
                description=desc, effective_time=eff_time,
            ))
        session.flush()

        # Run simulation
        meta = session.query(SimulationMetadata).first()
        runner = SimulationRunner(meta.start_datetime, meta.end_datetime, session)
        runner.simulate(session)

    return jsonify({"name": sim_name, "message": "seeded"}), 201
