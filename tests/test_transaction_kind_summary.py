from datetime import date
from decimal import Decimal

from kharchalens.analytics import spending_by_transaction_kind
from kharchalens.models import (
    Transaction,
    TransactionKind,
    TransactionType,
)


def test_spending_by_transaction_kind():

    transactions = [

        Transaction(
            date=date.today(),
            narration="Amazon",
            amount=Decimal(100),
            transaction_type=TransactionType.DEBIT,
            kind=TransactionKind.PURCHASE,
        ),

        Transaction(
            date=date.today(),
            narration="PPF",
            amount=Decimal(200),
            transaction_type=TransactionType.DEBIT,
            kind=TransactionKind.INVESTMENT,
        ),

        Transaction(
            date=date.today(),
            narration="ATM",
            amount=Decimal(50),
            transaction_type=TransactionType.DEBIT,
            kind=TransactionKind.CASH_WITHDRAWAL,
        ),
    ]

    summary = spending_by_transaction_kind(
        transactions
    )

    assert summary[TransactionKind.PURCHASE] == Decimal(100)
    assert summary[TransactionKind.INVESTMENT] == Decimal(200)
    assert summary[TransactionKind.CASH_WITHDRAWAL] == Decimal(50)