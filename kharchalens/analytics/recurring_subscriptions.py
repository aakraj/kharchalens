from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from kharchalens.models import Transaction, TransactionType

_MIN_GAP_DAYS = 21
_MAX_GAP_DAYS = 45
_AMOUNT_TOLERANCE = Decimal("0.15")
_MIN_STABILITY = Decimal("0.6")
_MIN_OCCURRENCES = 2


@dataclass(slots=True)
class RecurringSubscription:

    merchant: str

    amount: Decimal

    occurrences: int

    interval_days: int

    monthly_cost: Decimal

    annual_cost: Decimal


def _identity(transaction: Transaction) -> str:
    if transaction.merchant and transaction.merchant != "Unknown":
        return transaction.merchant
    return transaction.narration


def _typical_amount(amounts: list[Decimal]) -> Decimal:
    buckets: dict[Decimal, int] = defaultdict(int)
    for amount in amounts:
        bucket = (
            amount / Decimal(10)
        ).to_integral_value(rounding="ROUND_HALF_UP") * Decimal(10)
        buckets[bucket] += 1
    return max(buckets.items(), key=lambda item: item[1])[0]


def _median(amounts: list[Decimal]) -> Decimal:
    ordered = sorted(amounts)
    return ordered[len(ordered) // 2]


def _is_stable(amounts: list[Decimal], typical: Decimal) -> bool:
    if not typical:
        return False
    matched = sum(
        1 for amount in amounts
        if abs(amount - typical) <= _AMOUNT_TOLERANCE * typical
    )
    return (Decimal(matched) / Decimal(len(amounts))) >= _MIN_STABILITY


def recurring_subscriptions(
        transactions: list[Transaction],
) -> list[RecurringSubscription]:
    """Flag debits that repeat to the same merchant at a ~monthly cadence.

    A merchant qualifies when it has at least two debits whose consecutive
    day-gaps all fall within ``[_MIN_GAP_DAYS, _MAX_GAP_DAYS]`` and whose
    amounts stay within a tolerance of the typical (mode-rounded) amount.
    """
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for transaction in transactions:
        if transaction.transaction_type != TransactionType.DEBIT:
            continue
        grouped[_identity(transaction)].append(transaction)

    result: list[RecurringSubscription] = []
    for merchant, txns in grouped.items():
        if len(txns) < _MIN_OCCURRENCES:
            continue

        ordered = sorted(txns, key=lambda t: t.date)
        gaps = [
            (ordered[index + 1].date - ordered[index].date).days
            for index in range(len(ordered) - 1)
        ]
        if min(gaps) < _MIN_GAP_DAYS or max(gaps) > _MAX_GAP_DAYS:
            continue

        amounts = [t.amount for t in ordered]
        if not _is_stable(amounts, _typical_amount(amounts)):
            continue

        amount = _median(amounts)
        interval_days = sorted(gaps)[len(gaps) // 2]
        annual = amount * (Decimal(365) / Decimal(interval_days))
        result.append(
            RecurringSubscription(
                merchant=merchant,
                amount=amount,
                occurrences=len(ordered),
                interval_days=interval_days,
                monthly_cost=amount,
                annual_cost=annual.to_integral_value(
                    rounding="ROUND_HALF_UP",
                ),
            )
        )

    result.sort(key=lambda item: item.annual_cost, reverse=True)
    return result