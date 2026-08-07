from __future__ import annotations

import re
from decimal import Decimal
from typing import ClassVar

from kharchalens.models import Transaction, TransactionType

from .hdfc_base import HdfcStatementParser

# Amounts in SBI statements may carry a Dr/Cr suffix (or stand next to the
# ₹ symbol in the column header). The suffix is not part of the numeric value.
_DR_CR_SUFFIX = re.compile(
    r"\s*(?:dr|cr|debit|credit)\s*$",
    re.IGNORECASE,
)


class SbiStatementParser(HdfcStatementParser):
    """Shared row-parsing logic for SBI statements (Excel and PDF).

    Reuses the generic cell/date/amount helpers from the base parser and
    only special-cases SBI's own amounts (which can trail a ``Dr``/``Cr``
    suffix) and its column names.
    """

    #: Headers found on an SBI statement are normalised against these
    #: canonical names via :meth:`_column_for_header`.
    _CANONICAL_ALIASES: ClassVar[dict[str, str]] = {
        "value": "value_date",
        "valuedate": "value_date",
        "value date": "value_date",
        "postdate": "post_date",
        "post date": "post_date",
        "txndate": "post_date",
        "txn date": "post_date",
        "transactiondate": "post_date",
        "transaction date": "post_date",
        "details": "details",
        "narration": "details",
        "description": "details",
        "particulars": "details",
        "transactionremarks": "details",
        "transaction remarks": "details",
        "refnochequeno": "ref",
        "refno": "ref",
        "cheque": "ref",
        "chqrefno": "ref",
        "chqnoref": "ref",
        "chqref": "ref",
        "refnumber": "ref",
        "ref.no": "ref",
        "debit": "debit",
        "withdrawal": "debit",
        "withdrawalamt": "debit",
        "debitamt": "debit",
        "dr": "debit",
        "credit": "credit",
        "deposit": "credit",
        "depositamt": "credit",
        "creditamt": "credit",
        "cr": "credit",
        "balance": "balance",
        "closingbalance": "balance",
        "runningbalance": "balance",
        "availablebalance": "balance",
    }

    #: Multi-word synonyms not covered by a single normalised token.
    _EXTRA_DATE_ALIASES: ClassVar[dict[str, str]] = {
        "dated": "value_date",
        "date": "post_date",
    }

    @staticmethod
    def _normalize_header(header: str) -> str:
        """Lowercase a header and drop the rupee symbol and punctuation."""
        return (
            "".join(
                character
                for character in header
                if character.isalnum() or character.isspace()
            )
            .lower()
            .strip()
        )

    def _column_for_header(self, header: str) -> str | None:
        """Map a header string to a canonical SBI column name."""
        text = self._normalize_header(header)
        text = text.replace("₹", "").strip()

        if text in self._CANONICAL_ALIASES:
            return self._CANONICAL_ALIASES[text]

        if text in self._EXTRA_DATE_ALIASES:
            return self._EXTRA_DATE_ALIASES[text]

        # Remove spaces to catch variants like "ValueDate".
        compact = text.replace(" ", "")
        if compact in self._CANONICAL_ALIASES:
            return self._CANONICAL_ALIASES[compact]

        return None

    @classmethod
    def _strip_dr_cr(cls, value: object) -> str:
        """Remove a trailing Dr/Cr indicator from an amount cell."""
        cleaned = cls._clean_cell(value).replace("₹", "").strip()
        return _DR_CR_SUFFIX.sub("", cleaned) or ""

    def _parse_amount(self, value: object) -> Decimal | None:
        return super()._parse_amount(self._strip_dr_cr(value))

    def _parse_row(self, row: dict[str, object]) -> Transaction | None:
        # Prefer the posted (valued) date; fall back to the value date.
        date_value = self._clean_cell(row.get("post_date"))
        if not date_value:
            date_value = self._clean_cell(row.get("value_date"))
        if not date_value:
            date_value = self._clean_cell(row.get("date"))

        narration = self._clean_cell(row.get("details"))

        if not date_value or not narration:
            return None

        transaction_date = self._parse_date(date_value)

        if transaction_date is None:
            return None

        withdrawal = self._parse_amount(row.get("debit"))
        deposit = self._parse_amount(row.get("credit"))

        if withdrawal is not None and withdrawal != Decimal(0):
            amount = withdrawal
            transaction_type = TransactionType.DEBIT
        elif deposit is not None and deposit != Decimal(0):
            amount = deposit
            transaction_type = TransactionType.CREDIT
        else:
            return None

        reference = self._clean_cell(row.get("ref")) or None
        balance = self._parse_amount(row.get("balance"))

        return Transaction(
            date=transaction_date,
            narration=narration,
            amount=amount,
            transaction_type=transaction_type,
            balance=balance,
            reference_number=reference,
        )