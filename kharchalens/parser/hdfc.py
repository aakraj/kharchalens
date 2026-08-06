from __future__ import annotations

from pathlib import Path

import pandas as pd

from kharchalens.models import Transaction

from .hdfc_base import HdfcStatementParser


class HdfcParser(HdfcStatementParser):
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

        rows = [
            {
                "Date": row.get("Date"),
                "Narration": row.get("Narration"),
                "Chq./Ref.No.": row.get("Chq./Ref.No."),
                "Withdrawal Amt.": row.get("Withdrawal Amt."),
                "Deposit Amt.": row.get("Deposit Amt."),
                "Closing Balance": row.get("Closing Balance"),
            }
            for _, row in df.iterrows()
        ]

        return self._rows_to_transactions(rows)

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