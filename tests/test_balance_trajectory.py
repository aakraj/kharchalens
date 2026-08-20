from datetime import date
from decimal import Decimal

from kharchalens.analytics import BalancePoint, balance_trajectory
from kharchalens.models import Transaction, TransactionType


def test_balance_trajectory_uses_recorded_balance():

    transactions = [
        Transaction(
            date=date(2025, 1, 5),
            narration="SALARY",
            amount=Decimal(50000),
            transaction_type=TransactionType.CREDIT,
            balance=Decimal(50000),
        ),
        Transaction(
            date=date(2025, 1, 10),
            narration="AMAZON",
            amount=Decimal(2000),
            transaction_type=TransactionType.DEBIT,
            balance=Decimal(48000),
        ),
    ]

    points = balance_trajectory(transactions)

    assert points == [
        BalancePoint(date=date(2025, 1, 5), balance=Decimal(50000)),
        BalancePoint(date=date(2025, 1, 10), balance=Decimal(48000)),
    ]


def test_balance_trajectory_carries_last_known_balance_forward():

    transactions = [
        Transaction(
            date=date(2025, 1, 5),
            narration="SALARY",
            amount=Decimal(50000),
            transaction_type=TransactionType.CREDIT,
            balance=Decimal(50000),
        ),
        Transaction(
            date=date(2025, 1, 8),
            narration="GROCERY",
            amount=Decimal(1000),
            transaction_type=TransactionType.DEBIT,
            balance=None,
        ),
    ]

    points = balance_trajectory(transactions)

    assert points[-1].date == date(2025, 1, 8)
    assert points[-1].balance == Decimal(49000)


def test_balance_trajectory_falls_back_to_cumulative_net():

    transactions = [
        Transaction(
            date=date(2025, 1, 5),
            narration="SALARY",
            amount=Decimal(10000),
            transaction_type=TransactionType.CREDIT,
        ),
        Transaction(
            date=date(2025, 1, 8),
            narration="BILL",
            amount=Decimal(3000),
            transaction_type=TransactionType.DEBIT,
        ),
    ]

    points = balance_trajectory(transactions)

    assert points == [
        BalancePoint(date=date(2025, 1, 5), balance=Decimal(10000)),
        BalancePoint(date=date(2025, 1, 8), balance=Decimal(7000)),
    ]


def test_balance_trajectory_empty():

    assert balance_trajectory([]) == []