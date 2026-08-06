from datetime import date
from decimal import Decimal

from kharchalens.analytics import top_merchants
from kharchalens.models import Transaction, TransactionType


def test_top_merchants():

    transactions = [

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(500),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(1000),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(400),
            transaction_type=TransactionType.DEBIT,
            merchant="Zomato",
        ),

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(200),
            transaction_type=TransactionType.CREDIT,
            merchant="Amazon",
        ),
    ]

    result = top_merchants(transactions)

    assert result[0][0] == "Amazon"
    assert result[0][1] == Decimal(1500)

    assert result[1][0] == "Zomato"