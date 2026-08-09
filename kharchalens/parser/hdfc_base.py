from __future__ import annotations

import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

import pandas as pd

from kharchalens.models import Transaction, TransactionType

from .base import StatementParser


class ExcelPasswordRequired(ValueError):
    """The statement workbook is encrypted and no password was supplied."""


class ExcelIncorrectPassword(ValueError):
    """The supplied password did not decrypt the statement workbook."""


def _is_encrypted_container(file_path: str) -> bool:
    try:
        import msoffcrypto

        with open(file_path, "rb") as handle:
            return bool(msoffcrypto.OfficeFile(handle).is_encrypted())
    except Exception:  # noqa: BLE001 - sniffing may fail on odd containers
        return False


def _read_plain_excel(file_path: str) -> pd.DataFrame:
    raw = Path(file_path).read_bytes()
    head = raw[:512].lstrip().lower()

    if head.startswith(b"pk\x03\x04"):
        return pd.read_excel(
            file_path,
            engine="openpyxl",
            header=None,
            dtype=object,
        )

    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return pd.read_excel(
            file_path,
            engine="xlrd",
            header=None,
            dtype=object,
        )

    raise ValueError(
        "Only Excel files (.xls / .xlsx) are currently supported."
    )


def _decrypt_excel(
        file_path: str,
        password: str,
) -> pd.DataFrame | None:
    """Decrypt a password-protected workbook; None when it isn't encrypted."""
    import msoffcrypto

    output = io.BytesIO()

    try:
        with open(file_path, "rb") as handle:
            office = msoffcrypto.OfficeFile(handle)

            if not office.is_encrypted():
                return None

            # No verify_password here: some creators (e.g. Apple Numbers)
            # write an agile verifier that rejects even the correct password.
            # We confirm the password below by checking the decrypted bytes.
            office.load_key(password=password)
            office.decrypt(output)
    except (
        msoffcrypto.exceptions.InvalidKeyError,
        msoffcrypto.exceptions.DecryptionError,
        msoffcrypto.exceptions.FileFormatError,
    ) as exc:
        raise ExcelIncorrectPassword(
            "The password did not decrypt this Excel statement."
        ) from exc

    output.seek(0)
    try:
        return pd.read_excel(
            output,
            engine="openpyxl",
            header=None,
            dtype=object,
        )
    except Exception as exc:  # garbage bytes mean wrong key
        raise ExcelIncorrectPassword(
            "The password did not decrypt this Excel statement."
        ) from exc


def read_excel_like(
        file_path: str,
        password: str | None = None,
) -> pd.DataFrame:
    """Read a workbook, decrypting it first when a password is supplied."""
    if password is not None:
        decrypted = _decrypt_excel(file_path, password)
        if decrypted is not None:
            return decrypted
        return _read_plain_excel(file_path)

    if _is_encrypted_container(file_path):
        raise ExcelPasswordRequired(
            "This Excel statement is password-protected. "
            "Enter its password to continue."
        )

    return _read_plain_excel(file_path)


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
            "%d.%m.%Y",
            "%d.%m.%y",
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
