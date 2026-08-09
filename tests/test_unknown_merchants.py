from datetime import date
from decimal import Decimal

from kharchalens.analytics import top_unknown_merchants
from kharchalens.models import Transaction, TransactionType


def test_top_unknown_merchants():

    transactions = [

        Transaction(
            date=date.today(),
            narration="ABC",
            amount=Decimal(10),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="ABC",
            amount=Decimal(20),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="XYZ",
            amount=Decimal(20),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="AMAZON",
            amount=Decimal(30),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),
    ]

    result = top_unknown_merchants(transactions)

    assert result[0] == ("ABC", 2)
    assert result[1] == ("XYZ", 1)


def test_top_unknown_merchants_ignores_credits_and_known():
    transactions = [
        Transaction(
            date=date.today(),
            narration="SALARY",
            amount=Decimal("50000.00"),
            transaction_type=TransactionType.CREDIT,
            merchant="Unknown",
        ),
        Transaction(
            date=date.today(),
            narration="AMAZON",
            amount=Decimal("30.00"),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),
        Transaction(
            date=date.today(),
            narration="HIDDEN",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),
    ]

    result = top_unknown_merchants(transactions)

    assert result == [("HIDDEN", 1)]


def test_top_unknown_merchants_respects_limit():
    transactions = [
        Transaction(
            date=date.today(),
            narration=f"N{n}",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        )
        for n in range(5)
    ]

    result = top_unknown_merchants(transactions, limit=2)

    assert len(result) == 2