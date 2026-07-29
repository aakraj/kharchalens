from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from kharchalens.models import Transaction, TransactionType

from .base import StatementParser


class HdfcParser(StatementParser):
    REQUIRED_COLUMNS = {
        "Date",
        "Narration",
        "Chq./Ref.No.",
        "Withdrawal Amt.",
        "Deposit Amt.",
    }

    def parse(self, file_path: str) -> list[Transaction]:
        raw_df = self._read_statement(file_path)
        header_row = self._find_header_row(raw_df)

        if header_row is None:
            raise ValueError(
                "We could not find the transaction table in this HDFC statement."
            )

        df = self._prepare_transaction_table(raw_df, header_row)
        self._validate_columns(df)

        transactions: list[Transaction] = []

        for _, row in df.iterrows():
            transaction = self._parse_row(row)

            if transaction is not None:
                transactions.append(transaction)

        if not transactions:
            raise ValueError(
                "The statement was recognised, but no valid transactions were found."
            )

        return transactions

    @staticmethod
    def _read_statement(file_path: str) -> pd.DataFrame:
        suffix = Path(file_path).suffix.lower()

        if suffix == ".xls":
            return pd.read_excel(
                file_path,
                engine="xlrd",
                header=None,
                dtype=object,
            )

        if suffix == ".xlsx":
            return pd.read_excel(
                file_path,
                engine="openpyxl",
                header=None,
                dtype=object,
            )

        raise ValueError("Only .xls and .xlsx files are currently supported.")

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

    def _find_header_row(self, raw_df: pd.DataFrame) -> int | None:
        for row_index, row in raw_df.iterrows():
            cleaned_values = {
                self._clean_cell(value)
                for value in row.tolist()
                if self._clean_cell(value)
            }

            if {"Date", "Narration"}.issubset(cleaned_values):
                return int(row_index)

        return None

    def _prepare_transaction_table(
            self,
            raw_df: pd.DataFrame,
            header_row: int,
    ) -> pd.DataFrame:
        header = [
            self._clean_cell(value)
            for value in raw_df.iloc[header_row].tolist()
        ]

        df = raw_df.iloc[header_row + 1 :].copy()
        df.columns = header

        # Remove unnamed/blank columns.
        df = df.loc[:, [column != "" for column in df.columns]]

        # Remove fully empty rows.
        df = df.dropna(how="all")

        # Clean all column names again for safety.
        df.columns = [
            self._clean_cell(column)
            for column in df.columns
        ]

        # Remove repeated transaction headers found on later pages.
        if "Date" in df.columns:
            df = df[
                df["Date"].apply(self._clean_cell).str.lower() != "date"
                ]

        return df

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing = sorted(self.REQUIRED_COLUMNS - set(df.columns))

        if missing:
            raise ValueError(
                "The HDFC transaction table was found, "
                f"but these columns are missing: {missing}"
            )

    def _parse_row(self, row: pd.Series) -> Transaction | None:
        date_value = self._clean_cell(row.get("Date"))
        narration = self._clean_cell(row.get("Narration"))

        if not date_value or not narration:
            return None

        transaction_date = self._parse_date(date_value)

        if transaction_date is None:
            return None

        withdrawal = self._parse_amount(row.get("Withdrawal Amt."))
        deposit = self._parse_amount(row.get("Deposit Amt."))

        if withdrawal is not None and withdrawal != Decimal("0"):
            amount = withdrawal
            transaction_type = TransactionType.DEBIT
        elif deposit is not None and deposit != Decimal("0"):
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
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue

        try:
            parsed = pd.to_datetime(value, dayfirst=True, errors="raise")
            return parsed.date()
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