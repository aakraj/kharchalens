from decimal import Decimal

from kharchalens.models import Transaction, TransactionType


def format_inr(amount: Decimal) -> str:
    """
    Formats currency using the Indian numbering system.

    Examples:
        1250 -> ₹1,250
        125000 -> ₹1.25 L
        5200000 -> ₹52.00 L
        145000000 -> ₹14.50 Cr
    """

    value = float(amount)

    if abs(value) >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:.2f} Cr"

    if abs(value) >= 1_00_000:
        return f"₹{value / 1_00_000:.2f} L"

    return f"₹{value:,.0f}"


def build_summary(transactions: list[Transaction]) -> dict:
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for transaction in transactions:
        if transaction.transaction_type == TransactionType.DEBIT:
            total_debit += transaction.amount
        else:
            total_credit += transaction.amount

    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net_cash_flow": total_credit - total_debit,
        "transaction_count": len(transactions),
    }