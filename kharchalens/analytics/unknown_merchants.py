from __future__ import annotations

from collections import Counter

from kharchalens.models import Transaction


def top_unknown_merchants(
        transactions: list[Transaction],
        limit: int = 20,
) -> list[tuple[str, int]]:
    """
    Returns the most common unknown merchant narrations.
    """

    counter: Counter[str] = Counter()

    for transaction in transactions:

        if transaction.merchant != "Unknown":
            continue

        counter[transaction.narration] += 1

    return counter.most_common(limit)