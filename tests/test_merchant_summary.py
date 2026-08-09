from datetime import date
from decimal import Decimal

from kharchalens.analytics.merchant_summary import merchant_summary
from kharchalens.models import Transaction, TransactionKind, TransactionType


def _txn(
        day: int,
        amount: str,
        merchant: str | None = None,
        type_: TransactionType = TransactionType.DEBIT,
) -> Transaction:
    return Transaction(
        date=date(2026, 1, day),
        narration="test",
        amount=Decimal(amount),
        transaction_type=type_,
        merchant=merchant,
    )


def test_aggregates_spend_totals_and_averages():
    rows = merchant_summary(
        [
            _txn(1, "100.00", "Swiggy"),
            _txn(2, "50.00", "Swiggy"),
            _txn(3, "200.00", "Zomato"),
        ]
    )

    assert rows[0]["Merchant"] == "Zomato"
    assert rows[0]["Spend"] == Decimal("200.00")
    assert rows[0]["Transactions"] == 1
    assert rows[0]["Average"] == Decimal("200.00")

    assert rows[1]["Merchant"] == "Swiggy"
    assert rows[1]["Spend"] == Decimal("150.00")
    assert rows[1]["Transactions"] == 2
    assert rows[1]["Average"] == Decimal("75.00")


def test_unknown_merchant_maps_to_needs_review():
    rows = merchant_summary(
        [
            _txn(1, "100.00", "Unknown"),
            _txn(2, "50.00", None),
        ]
    )

    assert len(rows) == 1
    assert rows[0]["Merchant"] == "🟡 Needs Review"
    assert rows[0]["Spend"] == Decimal("150.00")


def test_credit_transactions_excluded():
    rows = merchant_summary(
        [
            _txn(1, "100.00", "Swiggy"),
            _txn(2, "5000.00", "Salary", TransactionType.CREDIT),
        ]
    )

    assert len(rows) == 1
    assert rows[0]["Spend"] == Decimal("100.00")


def test_limit_slices_top_n():
    rows = merchant_summary(
        [
            _txn(1, "300.00", "Amazon"),
            _txn(2, "200.00", "Flipkart"),
            _txn(3, "100.00", "Myntra"),
        ],
        limit=2,
    )

    assert [r["Merchant"] for r in rows] == ["Amazon", "Flipkart"]


def test_limit_none_returns_all():
    rows = merchant_summary(
        [
            _txn(1, "300.00", "Amazon"),
            _txn(2, "200.00", "Flipkart"),
        ],
        limit=None,
    )

    assert len(rows) == 2


def test_empty_transactions():
    assert merchant_summary([]) == []


def test_merchant_kind_mobility():
    txn = _txn(1, "100.00", "Swiggy")
    txn.kind = TransactionKind.PURCHASE

    rows = merchant_summary([txn])

    assert rows[0]["Merchant"] == "Swiggy"