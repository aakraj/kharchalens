from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .enums import TransactionType
from .transaction_kind import TransactionKind


@dataclass(slots=True)
class Transaction:
    """Represents a single bank transaction."""

    date: date
    narration: str
    amount: Decimal
    transaction_type: TransactionType

    balance: Decimal | None = None
    reference_number: str | None = None

    merchant: str | None = None
    category: str | None = None
    subcategory: str | None = None
    kind: TransactionKind = TransactionKind.UNKNOWN