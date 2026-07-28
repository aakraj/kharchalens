from datetime import date
from decimal import Decimal

from kharchalens.models import Transaction, TransactionType


def test_create_transaction():
    transaction = Transaction(
        date=date(2025, 4, 1),
        narration="UPI AMAZON",
        amount=Decimal("499.99"),
        transaction_type=TransactionType.DEBIT,
    )

    assert transaction.date == date(2025, 4, 1)
    assert transaction.amount == Decimal("499.99")
    assert transaction.transaction_type == TransactionType.DEBIT
    assert transaction.merchant is None