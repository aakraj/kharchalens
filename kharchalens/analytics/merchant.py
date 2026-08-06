from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from kharchalens.models import Transaction, TransactionType


def _display_name(transaction: Transaction) -> str:
    """
    Name shown in the Top Merchants chart.

    Recognized merchants keep their resolved name.

    Unknown merchants are shown using their original narration so that
    high-value expenses are never hidden behind a single 'Unknown' bar.
    """

    if (transaction.merchant
            and transaction.merchant != "Unknown"):
        return transaction.merchant

    return "🟡 Needs Review"


def top_merchants(
        transactions: list[Transaction],
        limit: int | None = 10,
) -> list[tuple[str, Decimal]]:
    """
    Returns merchants ranked by debit spending.

    Unknown merchants are grouped using their narration so they appear
    individually instead of as one large 'Unknown' bucket.
    """

    totals: dict[str, Decimal] = defaultdict(
        lambda: Decimal(0)
    )

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        merchant = _display_name(transaction)

        totals[merchant] += transaction.amount

    sorted_merchants = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    if limit is None:
        return sorted_merchants
    return sorted_merchants[:limit]