from datetime import date
from decimal import Decimal

from kharchalens.analytics import monthly_cash_flow
from kharchalens.models import Transaction, TransactionType


def test_monthly_cash_flow():

    transactions = [
        Transaction(
            date=date(2025, 1, 1),
            narration="SALARY",
            amount=Decimal(50000),
            transaction_type=TransactionType.CREDIT,
        ),
        Transaction(
            date=date(2025, 1, 10),
            narration="AMAZON",
            amount=Decimal(8000),
            transaction_type=TransactionType.DEBIT,
        ),
        Transaction(
            date=date(2025, 2, 1),
            narration="SALARY",
            amount=Decimal(50000),
            transaction_type=TransactionType.CREDIT,
        ),
        Transaction(
            date=date(2025, 2, 2),
            narration="NETFLIX",
            amount=Decimal(40000),
            transaction_type=TransactionType.DEBIT,
        ),
    ]

    rows = monthly_cash_flow(transactions)

    assert [row["Month"] for row in rows] == ["2025-01", "2025-02"]

    row_one = rows[0]
    assert row_one == {
        "Month": "2025-01",
        "Income": Decimal(50000),
        "Expense": Decimal(8000),
        "Savings": Decimal(42000),
    }

    assert rows[1]["Savings"] == Decimal(10000)


def test_monthly_cash_flow_empty_statement():

    assert monthly_cash_flow([]) == []


def test_monthly_cash_flow_negative_savings():

    transactions = [
        Transaction(
            date=date(2025, 1, 1),
            narration="SALARY",
            amount=Decimal(10000),
            transaction_type=TransactionType.CREDIT,
        ),
        Transaction(
            date=date(2025, 1, 15),
            narration="RENT",
            amount=Decimal(15000),
            transaction_type=TransactionType.DEBIT,
        ),
    ]

    rows = monthly_cash_flow(transactions)

    assert rows[0]["Savings"] == Decimal(-5000)