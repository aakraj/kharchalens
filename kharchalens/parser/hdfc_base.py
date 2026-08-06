from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast

import pandas as pd

from kharchalens.models import Transaction, TransactionType

from .base import StatementParser


class HdfcStatementParser(StatementParser):
    """Shared row-parsing logic for HDFC statements (Excel and PDF)."""

    @staticmethod
    def _clean_cell(value: object) -> str:
        if pd.isna(value):
            return ""

        text = str(value)

        # Remove control characters sometimes present in HDFC exports.
        return "".join(
            character
            for character in text
            if character.isprintable()
        ).strip()

    @staticmethod
    def _parse_date(value: str) -> date | None:
        supported_formats = (
            "%d/%m/%Y",
            "%d/%m/%y",
            "%d-%m-%Y",
            "%d-%m-%y",
        )

        for date_format in supported_formats:
            try:
                # Bank-statement dates are naive calendar dates; no tz applies.
                return datetime.strptime(value, date_format).date()  # noqa: DTZ007
            except ValueError:
                continue

        try:
            parsed: Any = pd.to_datetime(value, dayfirst=True, errors="raise")
            return cast(date, parsed.date())
        except (ValueError, TypeError):
            return None

    def _parse_amount(self, value: object) -> Decimal | None:
        cleaned = self._clean_cell(value)

        if not cleaned:
            return None

        cleaned = cleaned.replace(",", "").replace("₹", "").strip()

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _parse_row(self, row: dict[str, object]) -> Transaction | None:
        date_value = self._clean_cell(row.get("Date"))
        narration = self._clean_cell(row.get("Narration"))

        if not date_value or not narration:
            return None

        transaction_date = self._parse_date(date_value)

        if transaction_date is None:
            return None

        withdrawal = self._parse_amount(row.get("Withdrawal Amt."))
        deposit = self._parse_amount(row.get("Deposit Amt."))

        if withdrawal is not None and withdrawal != Decimal(0):
            amount = withdrawal
            transaction_type = TransactionType.DEBIT
        elif deposit is not None and deposit != Decimal(0):
            amount = deposit
            transaction_type = TransactionType.CREDIT
        else:
            return None

        reference = self._clean_cell(row.get("Chq./Ref.No.")) or None
        balance = self._parse_amount(row.get("Closing Balance"))

        return Transaction(
            date=transaction_date,
            narration=narration,
            amount=amount,
            transaction_type=transaction_type,
            balance=balance,
            reference_number=reference,
        )

    def _rows_to_transactions(
            self,
            rows: list[dict[str, object]],
    ) -> list[Transaction]:
        transactions: list[Transaction] = []

        for row in rows:
            transaction = self._parse_row(row)
            if transaction is not None:
                transactions.append(transaction)

        if not transactions:
            raise ValueError(
                "The statement was recognised, but no valid transactions were found."
            )

        return transactions
