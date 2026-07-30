from datetime import date
from decimal import Decimal

from kharchalens.analytics import top_unknown_merchants
from kharchalens.models import Transaction, TransactionType


def test_top_unknown_merchants():

    transactions = [

        Transaction(
            date=date.today(),
            narration="ABC",
            amount=Decimal("10"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="ABC",
            amount=Decimal("20"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="XYZ",
            amount=Decimal("20"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="AMAZON",
            amount=Decimal("30"),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),
    ]

    result = top_unknown_merchants(transactions)

    assert result[0] == ("ABC", 2)
    assert result[1] == ("XYZ", 1)