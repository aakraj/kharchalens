from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from kharchalens.models import Transaction, TransactionType


def top_merchants(
        transactions: list[Transaction],
        limit: int = 10,
) -> list[tuple[str, Decimal]]:
    """
    Returns merchants ranked by debit spending.
    """

    totals: dict[str, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        if not transaction.merchant:
            continue

        if transaction.merchant == "Unknown":
            continue

        totals[transaction.merchant] += transaction.amount

    return sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:limit]