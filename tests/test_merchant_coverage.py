from datetime import date
from decimal import Decimal

from kharchalens.analytics import merchant_coverage
from kharchalens.models import Transaction, TransactionType


def test_merchant_coverage():

    transactions = [

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(100),
            transaction_type=TransactionType.DEBIT,
            merchant="Amazon",
        ),

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(100),
            transaction_type=TransactionType.DEBIT,
            merchant="Unknown",
        ),

        Transaction(
            date=date.today(),
            narration="",
            amount=Decimal(100),
            transaction_type=TransactionType.DEBIT,
            merchant=None,
        ),
    ]

    coverage = merchant_coverage(transactions)

    assert coverage.recognized == 1
    assert coverage.unknown == 2
    assert coverage.total == 3
    assert round(coverage.coverage, 2) == 33.33


def test_merchant_coverage_empty():
    coverage = merchant_coverage([])

    assert coverage.recognized == 0
    assert coverage.unknown == 0
    assert coverage.total == 0
    assert coverage.coverage == 0.0