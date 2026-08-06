from __future__ import annotations

from collections import defaultdict

from kharchalens.models import Transaction
from kharchalens.models import TransactionType


def top_unknown_merchants(
        transactions: list[Transaction],
        limit: int = 20,
) -> list[tuple[str, int]]:

    counts: dict[str, int] = defaultdict(int)

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        if transaction.merchant != "Unknown":
            continue

        counts[transaction.narration] += 1

    return sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:limit]