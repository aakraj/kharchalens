from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from kharchalens.models import (
    Transaction,
    TransactionType,
)


def merchant_summary(
        transactions: list[Transaction],
        limit: int = 10,
):
    totals = defaultdict(lambda: Decimal("0"))
    counts = defaultdict(int)

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        merchant = transaction.merchant or "🟡 Needs Review"
        if merchant == "Unknown":
            merchant = "🟡 Needs Review"

        totals[merchant] += transaction.amount
        counts[merchant] += 1

    rows = []
    for merchant in totals:
        rows.append(
            {
                "Merchant": merchant,
                "Spend": totals[merchant],
                "Transactions": counts[merchant],
                "Average": totals[merchant] / counts[merchant],
            }
        )

    rows.sort(key=lambda row: row["Spend"], reverse=True)
    if limit is not None:
        rows = rows[:limit]
    return rows