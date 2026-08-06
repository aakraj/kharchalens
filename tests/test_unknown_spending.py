from datetime import date
from decimal import Decimal

from kharchalens.analytics import unknown_spending
from kharchalens.models import Transaction, TransactionType


def test_unknown_spending():

    transactions = [

        Transaction(
            date=date.today(),
            narration="SHOP A",
            amount=Decimal("100"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="SHOP A",
            amount=Decimal("300"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="SHOP B",
            amount=Decimal("250"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="AMAZON",
            amount=Decimal("500"),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),
    ]

    result = unknown_spending(transactions)

    assert len(result) == 2

    assert result[0].narration == "SHOP A"
    assert result[0].transactions == 2
    assert result[0].total_spend == Decimal("400")

    assert result[1].narration == "SHOP B"