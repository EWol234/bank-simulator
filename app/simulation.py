"""Simulation engine: propagators and runner."""

from datetime import datetime
from typing import NamedTuple
from abc import ABC, abstractmethod

from app.database import BalanceEntry


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


class SimulationRunner:
    def __init__(self, start_datetime, end_datetime):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.processing_queue = []
        self.listeners = dict()

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
                    if new_entry.effective_time >= timestamp:
                        self.processing_queue.append(listener)

        return None
