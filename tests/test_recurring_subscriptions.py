from datetime import date
from decimal import Decimal

from kharchalens.analytics import recurring_subscriptions
from kharchalens.models import Transaction, TransactionType


def _debit(day, month, amount: str, merchant: str, narration: str = "NAR"):

    return Transaction(
        date=date(2025, month, day),
        narration=narration,
        amount=Decimal(amount),
        transaction_type=TransactionType.DEBIT,
        merchant=merchant,
    )


def test_monthly_subscription_detected():

    transactions = [
        _debit(1, 1, "199", "Netflix"),
        _debit(1, 2, "199", "Netflix"),
        _debit(1, 3, "199", "Netflix"),
        _debit(1, 4, "199", "Netflix"),
    ]

    subscriptions = recurring_subscriptions(transactions)

    assert len(subscriptions) == 1
    netflix = subscriptions[0]
    assert netflix.merchant == "Netflix"
    assert netflix.amount == Decimal(199)
    assert netflix.occurrences == 4
    assert netflix.interval_days == 31
    assert netflix.monthly_cost == Decimal(199)
    assert netflix.annual_cost == Decimal(2343)


def test_weekly_merchant_not_recurring():

    transactions = [
        _debit(1, 1, "500", "Cafe"),
        _debit(8, 1, "500", "Cafe"),
        _debit(15, 1, "500", "Cafe"),
        _debit(22, 1, "500", "Cafe"),
    ]

    assert recurring_subscriptions(transactions) == []


def test_seasonal_gap_not_recurring():

    transactions = [
        _debit(1, 1, "1000", "Gym"),
        _debit(1, 4, "1000", "Gym"),
    ]

    assert recurring_subscriptions(transactions) == []


def test_unstable_amount_not_recurring():

    transactions = [
        _debit(1, 1, "100", "Electricity"),
        _debit(1, 2, "400", "Electricity"),
        _debit(1, 3, "150", "Electricity"),
    ]

    assert recurring_subscriptions(transactions) == []


def test_unknown_merchant_grouped_by_narration():

    transactions = [
        _debit(1, 1, "299", "Unknown", narration="SPOTIFY PAYMENT"),
        _debit(1, 2, "299", "Unknown", narration="SPOTIFY PAYMENT"),
    ]

    subscriptions = recurring_subscriptions(transactions)

    assert len(subscriptions) == 1
    assert subscriptions[0].merchant == "SPOTIFY PAYMENT"


def test_empty_transactions():

    assert recurring_subscriptions([]) == []