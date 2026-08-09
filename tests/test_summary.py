from datetime import date
from decimal import Decimal

from kharchalens.dashboard.summary import build_summary
from kharchalens.models import Transaction, TransactionType


def _txn(day: int, amount: str, type_: TransactionType) -> Transaction:
    return Transaction(
        date=date(2026, 1, day),
        narration="test",
        amount=Decimal(amount),
        transaction_type=type_,
    )


def test_average_monthly_spend_single_month():
    summary = build_summary(
        [
            _txn(1, "100.00", TransactionType.DEBIT),
            _txn(15, "50.00", TransactionType.DEBIT),
        ]
    )

    assert summary["month_count"] == 1
    assert summary["average_monthly_spend"] == Decimal("150.00")


def test_average_monthly_spread_across_months():
    feb = Transaction(
        date=date(2026, 2, 5),
        narration="test",
        amount=Decimal("2000.00"),
        transaction_type=TransactionType.DEBIT,
    )
    summary = build_summary(
        [
            _txn(1, "6000.00", TransactionType.DEBIT),
            _txn(1, "3000.00", TransactionType.DEBIT),
            _txn(1, "3000.00", TransactionType.CREDIT),
            feb,
        ]
    )

    assert summary["month_count"] == 2
    assert summary["average_monthly_spend"] == Decimal("5500.00")


def test_average_monthly_spend_no_debits():
    summary = build_summary(
        [_txn(1, "1000.00", TransactionType.CREDIT)]
    )

    assert summary["month_count"] == 1
    assert summary["average_monthly_spend"] == Decimal(0)