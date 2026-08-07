from __future__ import annotations

import pandas as pd

from kharchalens.models import Transaction

from .hdfc_base import read_excel_like
from .sbi_base import SbiStatementParser


class SbiParser(SbiStatementParser):
    """Parses SBI statement workbooks (.xls / .xlsx).

    The SBI header row is auto-detected by the presence of a date-style
    column and a ``Details``/``Narration`` column; each header name is then
    mapped to a canonical column via :meth:`_column_for_header`. SBI
    exports several layouts (with/without ``Value Date`` or ``₹`` symbols)
    so column names, not positions, are what matter here.
    """

    def parse(self, file_path: str, password: str | None = None) -> list[Transaction]:
        raw_df = self._read_statement(file_path, password=password)
        header_row = self._find_header_row(raw_df)

        if header_row is None:
            raise ValueError(
                "We could not find the transaction table in this SBI statement."
            )

        df = self._prepare_transaction_table(raw_df, header_row)

        rows = [
            {name: row[name] for name in df.columns}
            for _, row in df.iterrows()
        ]

        return self._rows_to_transactions(rows)

    @staticmethod
    def _read_statement(
            file_path: str,
            password: str | None = None,
    ) -> pd.DataFrame:
        return read_excel_like(file_path, password=password)

    def _find_header_row(self, raw_df: pd.DataFrame) -> int | None:
        expected_keys = {"post_date", "value_date", "date"}

        for row_index, row in raw_df.iterrows():
            column_map: set[str] = set()

            for value in row.tolist():
                canonical = self._column_for_header(self._clean_cell(value))
                if canonical:
                    column_map.add(canonical)

            has_date = bool(column_map & expected_keys)
            has_details = "details" in column_map

            if has_date and has_details:
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

        table = raw_df.iloc[header_row + 1 :].copy()

        # The position of each retained header maps back to the canonical name.
        by_index = {
            index: name
            for index, name in enumerate(self._column_for_header(col) for col in header)
            if name is not None
        }

        # Keep only columns whose header resolved to a canonical name.
        table = table.iloc[:, sorted(by_index)]
        table.columns = [by_index[index] for index in sorted(by_index)]

        # Drop fully empty rows and repeated SBI header rows on later pages.
        table = table.dropna(how="all")

        for column in table.columns:
            table[column] = [
                self._clean_cell(value)
                for value in table[column]
            ]

        date_keys = ("post_date", "value_date", "date")
        present = [name for name in date_keys if name in table.columns]
        if present:
            first = present[0]
            table = table[
                table[first].str.lower() != self._normalize_header(first)
            ]

        return table