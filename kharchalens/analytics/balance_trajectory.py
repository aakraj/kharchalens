from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from kharchalens.models import Transaction, TransactionType


@dataclass(slots=True)
class BalancePoint:

    date: date

    balance: Decimal


def balance_trajectory(
        transactions: list[Transaction],
) -> list[BalancePoint]:
    """Running balance over time, best-effort.

    Uses each statement's recorded ``balance`` when available (carrying the
    last known value forward across missing ones); otherwise falls back to a
    cumulative net (credits minus debits) starting from zero.
    """
    if not transactions:
        return []

    ordered = sorted(
        transactions,
        key=lambda t: (t.date, t.transaction_type.value),
    )

    has_balances = any(t.balance is not None for t in ordered)

    points: list[BalancePoint] = []
    running = Decimal(0)

    for txn in ordered:
        delta = (
            txn.amount
            if txn.transaction_type == TransactionType.CREDIT
            else -txn.amount
        )
        if has_balances and txn.balance is not None:
            running = txn.balance
        else:
            running += delta
        points.append(BalancePoint(date=txn.date, balance=running))

    return points