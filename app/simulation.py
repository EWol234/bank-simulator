"""Simulation engine: propagators and runner."""

from datetime import datetime, timedelta
from typing import NamedTuple
from abc import ABC, abstractmethod

from app.database import FundingRule, BalanceEntry, get_balance, get_balance_at_timestamp


class ListeningPoint(NamedTuple):
    account_id: int
    timestamp: datetime


class Propagator(ABC):
    @abstractmethod
    def listening_points(self):
        pass

    @abstractmethod
    def propagate(self, session):
        pass


class ManualEntry(Propagator):
    def __init__(self, account_id, amount, currency, timestamp, description="Manual entry"):
        self.account_id = account_id
        self.amount = amount
        self.currency = currency
        self.timestamp = timestamp
        self.description = description

    def listening_points(self):
        return []

    def propagate(self, session):
        balance_entry = BalanceEntry(
            account_id=self.account_id,
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            effective_time=self.timestamp,
        )
        session.add(balance_entry)
        session.flush()

        return [balance_entry]


class Topup(Propagator):
    def __init__(self, rule_id, target_account_id, source_account_id, timestamp, currency, threshold, target_amount):
        self.rule_id = rule_id
        self.target_account_id = target_account_id
        self.source_account_id = source_account_id
        self.currency = currency
        self.timestamp = timestamp
        self.threshold = threshold
        self.target_amount = target_amount
        self.description = f"{source_account_id} -> {target_account_id} Topup"

        self.funding_timestamp = timestamp + timedelta(minutes=30) # Hard-coding 30 mins for wires to land

    def listening_points(self):
        return [ListeningPoint(account_id=self.target_account_id, timestamp=self.timestamp)]

    def propagate(self, session):
        target_account_balance = get_balance(session, self.target_account_id, self.timestamp, self.currency)
        prior_topup_amount = get_balance_at_timestamp(session, self.target_account_id, self.funding_timestamp, self.currency, rule_id=self.rule_id)

        balance_diff = 0
        if target_account_balance > self.threshold:
            balance_diff = -min(prior_topup_amount, target_account_balance - self.threshold)
        elif target_account_balance < self.threshold:
            balance_diff = self.target_amount - target_account_balance - prior_topup_amount

        if balance_diff == 0:
            return []

        print(f"Target balance: {target_account_balance}, prior topup: {prior_topup_amount}, diff: {balance_diff}")

        source_balance_entry = BalanceEntry(
            account_id=self.source_account_id,
            amount=-balance_diff,
            currency=self.currency,
            description=self.description,
            effective_time=self.timestamp,
            rule_id=self.rule_id,
        )
        target_balance_entry = BalanceEntry(
            account_id=self.target_account_id,
            amount=balance_diff,
            currency=self.currency,
            description=self.description,
            effective_time=self.funding_timestamp,
            rule_id=self.rule_id,
        )

        session.add(source_balance_entry)
        session.add(target_balance_entry)
        session.flush()

        return [source_balance_entry, target_balance_entry]


class SweepOut(Propagator):
    def __init__(self, rule_id, target_account_id, source_account_id, timestamp, currency, threshold, target_amount):
        self.rule_id = rule_id
        self.target_account_id = target_account_id
        self.source_account_id = source_account_id
        self.currency = currency
        self.timestamp = timestamp
        self.threshold = threshold
        self.target_amount = target_amount
        self.description = f"{source_account_id} -> {target_account_id} Sweep Out"

        self.funding_timestamp = timestamp + timedelta(minutes=30)

    def listening_points(self):
        return [ListeningPoint(account_id=self.source_account_id, timestamp=self.timestamp)]

    def propagate(self, session):
        source_balance = get_balance(session, self.source_account_id, self.timestamp, self.currency)
        prior_sweep_amount = get_balance_at_timestamp(
            session, self.source_account_id, self.funding_timestamp, self.currency, rule_id=self.rule_id
        )
        # prior_sweep_amount is negative (debit entries on source) or zero

        balance_diff = 0
        if source_balance > self.threshold:
            # Sweep excess: bring source down to target_amount
            # prior_sweep_amount is negative, so adding it subtracts already-swept amount
            balance_diff = -(source_balance - self.target_amount + prior_sweep_amount)
        elif source_balance < self.threshold and prior_sweep_amount < 0:
            # Reversal: source dropped below threshold, undo some prior sweep
            balance_diff = min(-prior_sweep_amount, self.threshold - source_balance)

        if abs(balance_diff) < 1e-9:
            return []

        print(f"Source balance: {source_balance}, prior sweep: {prior_sweep_amount}, diff: {balance_diff}")

        source_balance_entry = BalanceEntry(
            account_id=self.source_account_id,
            amount=balance_diff,
            currency=self.currency,
            description=self.description,
            effective_time=self.funding_timestamp,
            rule_id=self.rule_id,
        )
        target_balance_entry = BalanceEntry(
            account_id=self.target_account_id,
            amount=-balance_diff,
            currency=self.currency,
            description=self.description,
            effective_time=self.funding_timestamp,
            rule_id=self.rule_id,
        )

        session.add(source_balance_entry)
        session.add(target_balance_entry)
        session.flush()

        return [source_balance_entry, target_balance_entry]


class SimulationRunner:
    def __init__(self, start_datetime, end_datetime, session):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.processing_queue = []
        self.listeners = dict()

        rules = session.query(FundingRule).all()
        current_date = start_datetime.date()
        end_date = end_datetime.date()

        while current_date <= end_date:
            for rule in rules:
                t = datetime.strptime(rule.time_of_day, "%H:%M:%S").time()
                timestamp = datetime.combine(current_date, t)
                if start_datetime <= timestamp <= end_datetime:
                    if rule.rule_type in ("TOPUP", "BACKUP_FUNDING"):
                        propagator = Topup(
                            rule_id=rule.id,
                            target_account_id=rule.target_account_id,
                            source_account_id=rule.source_account_id,
                            timestamp=timestamp,
                            currency=rule.currency,
                            threshold=rule.threshold,
                            target_amount=rule.target_amount,
                        )
                    elif rule.rule_type == "SWEEP_OUT":
                        propagator = SweepOut(
                            rule_id=rule.id,
                            target_account_id=rule.target_account_id,
                            source_account_id=rule.source_account_id,
                            timestamp=timestamp,
                            currency=rule.currency,
                            threshold=rule.threshold,
                            target_amount=rule.target_amount,
                        )
                    else:
                        continue
                    self.add_propagator(propagator)

            current_date += timedelta(days=1)


    def add_propagator(self, propagator):
        for listening_point in propagator.listening_points():
            self.listeners.setdefault(listening_point.account_id, []).append(
                (listening_point.timestamp, propagator)
            )

        self.processing_queue.append(propagator)

    def simulate(self, session):
        while self.processing_queue:
            propagator = self.processing_queue.pop(0)
            new_entries = propagator.propagate(session)

            for new_entry in new_entries:
                account_listeners = self.listeners.get(new_entry.account_id, [])
                for timestamp, listener in account_listeners:
                    if new_entry.effective_time <= timestamp:
                        self.processing_queue.append(listener)

        return None

