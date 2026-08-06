from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from kharchalens.models import Transaction
from kharchalens.models.enums import TransactionType


@dataclass(slots=True)
class UnknownMerchantSpend:

    narration: str

    transactions: int

    total_spend: Decimal


def unknown_spending(
        transactions: list[Transaction],
) -> list[UnknownMerchantSpend]:

    grouped: dict[str, UnknownMerchantSpend] = {}

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        if transaction.merchant != "Unknown":
            continue

        if transaction.narration not in grouped:

            grouped[transaction.narration] = UnknownMerchantSpend(
                narration=transaction.narration,
                transactions=0,
                total_spend=Decimal("0"),
            )

        item = grouped[transaction.narration]

        item.transactions += 1
        item.total_spend += transaction.amount

    return sorted(
        grouped.values(),
        key=lambda x: x.total_spend,
        reverse=True,
    )