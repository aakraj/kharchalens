from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import TypedDict

from kharchalens.models import (
    Transaction,
    TransactionType,
)


class MerchantSummaryRow(TypedDict):
    Merchant: str
    Spend: Decimal
    Transactions: int
    Average: Decimal


def merchant_summary(
        transactions: list[Transaction],
        limit: int | None = 10,
) -> list[MerchantSummaryRow]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    counts: dict[str, int] = defaultdict(int)

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        merchant = transaction.merchant or "🟡 Needs Review"
        if merchant == "Unknown":
            merchant = "🟡 Needs Review"

        totals[merchant] += transaction.amount
        counts[merchant] += 1

    rows: list[MerchantSummaryRow] = []
    for merchant, total in totals.items():
        rows.append(
            {
                "Merchant": merchant,
                "Spend": total,
                "Transactions": counts[merchant],
                "Average": total / counts[merchant],
            }
        )

    rows.sort(key=lambda row: row["Spend"], reverse=True)
    if limit is not None:
        rows = rows[:limit]
    return rows