from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import TypedDict

from kharchalens.models import Transaction, TransactionType


class MonthlyCashFlowRow(TypedDict):
    Month: str
    Income: Decimal
    Expense: Decimal
    Savings: Decimal


def monthly_cash_flow(
        transactions: list[Transaction],
) -> list[MonthlyCashFlowRow]:
    income: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    expense: dict[str, Decimal] = defaultdict(lambda: Decimal(0))

    for transaction in transactions:
        month = transaction.date.strftime("%Y-%m")
        if transaction.transaction_type == TransactionType.CREDIT:
            income[month] += transaction.amount
        else:
            expense[month] += transaction.amount

    months = sorted(set(income) | set(expense))
    return [
        {
            "Month": month,
            "Income": income.get(month, Decimal(0)),
            "Expense": expense.get(month, Decimal(0)),
            "Savings": (
                income.get(month, Decimal(0))
                - expense.get(month, Decimal(0))
            ),
        }
        for month in months
    ]