from __future__ import annotations

from kharchalens.models import Transaction
from kharchalens.models import TransactionKind


class TransactionClassifier:

    @staticmethod
    def classify(transaction: Transaction) -> None:

        text = transaction.narration.upper()

        if "ATM" in text or "ATW" in text:
            transaction.kind = TransactionKind.CASH_WITHDRAWAL
            return

        if (
            "PPF" in text
            or "SSY" in text
            or "ZERODHA" in text
            or "UPSTOX" in text
            or "JEWE" in text
            or "JEWEL" in text
            or "BILLDKINDIANCLEARING" in text
        ):
            transaction.kind = TransactionKind.INVESTMENT
            return

        if (
            "ICICIPRULIFE" in text
            or "MAX LIFE" in text
        ):
            transaction.kind = TransactionKind.INSURANCE
            return

        if (
            "SELF" in text
            or "WIFE" in text
            or "SHUBH RATNA" in text
            or "EXPENSES" in text
        ):
            transaction.kind = TransactionKind.TRANSFER
            return

        transaction.kind = TransactionKind.PURCHASE