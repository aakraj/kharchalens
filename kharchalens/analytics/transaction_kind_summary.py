from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from kharchalens.models import Transaction
from kharchalens.models import TransactionKind
from kharchalens.models import TransactionType


def spending_by_transaction_kind(
        transactions: list[Transaction],
) -> dict[TransactionKind, Decimal]:

    summary: dict[TransactionKind, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    for transaction in transactions:

        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        summary[transaction.kind] += transaction.amount

    return dict(summary)