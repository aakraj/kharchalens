from __future__ import annotations

import re
import traceback

import pdfplumber

from kharchalens.models import Transaction

from .hdfc_pdf import (
    HdfcPdfParser,
    PdfIncorrectPassword,
    PdfPasswordRequired,
    _column_for_word,
)
from .sbi_base import SbiStatementParser

_DATE_PATTERN = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")

_NUMERIC_PATTERN = re.compile(r"^₹?[\d,]+(?:\.\d+)?$")

_DATE_COLUMNS = frozenset({"value_date", "post_date"})

_AMOUNT_COLUMNS = frozenset({"debit", "credit"})

_FURNITURE_MARKERS = (
    "STATE BANK OF INDIA",
    "STATEMENT OF ACCOUNT",
    "ACCOUNT STATEMENT",
    "PAGE NO",
    "PAGE",
    "YOUR ACCOUNT",
    "BALANCE CARRIED",
    "TRANSACTIONS AS ON",
    "OPENING BALANCE",
)


class SbiPdfParser(SbiStatementParser):
    """Parses SBI e-statement PDFs using word positions.

    SBI transactions are placed under ``Post Date``/``Value Date``/``Details``
    and single-amount columns ``₹ Debit`` / ``₹ Credit``. As with HDFC PDFs,
    a blank debit or credit cell disappears from the raw text, so each value's
    column is recovered from its x-coordinate relative to the header row.
    """

    def parse(self, file_path: str, password: str | None = None) -> list[Transaction]:
        lines = self._extract_word_rows(file_path, password=password)

        if not lines:
            raise ValueError(
                "Could not extract any text from this PDF. It may be a "
                "scanned/image-only document."
            )

        rows = self._lines_to_transactions(lines)
        return self._rows_to_transactions(rows)

    def _extract_word_rows(
            self,
            file_path: str,
            password: str | None = None,
    ) -> list[list[tuple[float, float, float, str]]]:
        try:
            with pdfplumber.open(file_path, password=password or "") as pdf:
                lines: list[list[tuple[float, float, float, str]]] = []

                for page in pdf.pages:
                    words = page.extract_words()
                    lines.extend(HdfcPdfParser._group_words_by_line(words))

                return lines
        except Exception as exc:
            inner = exc.args[0] if exc.args else exc

            if type(inner).__name__ == "PDFPasswordIncorrect":
                if password:
                    raise PdfIncorrectPassword(
                        "The password did not decrypt this PDF statement."
                    ) from exc
                raise PdfPasswordRequired(
                    "This PDF statement is password-protected. Enter its "
                    "password to continue."
                ) from exc

            raise ValueError(
                "Could not read this PDF file. It may be damaged "
                f"or password-protected. ({type(exc).__name__}: {exc})\n"
                f"{traceback.format_exc()}"
            ) from exc

    def _header_columns(
            self,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> dict[str, tuple[float, float]] | None:
        for line in lines:
            first: dict[str, tuple[float, float]] = {}

            for word in line:
                canonical = self._column_for_header(word[3])
                if canonical and canonical not in first:
                    first[canonical] = (word[0], word[1])

            has_date = bool(set(first) & _DATE_COLUMNS)
            has_details = "details" in first
            has_amount = bool(set(first) & _AMOUNT_COLUMNS)

            if has_date and has_details and has_amount:
                return first

        return None

    @staticmethod
    def _suspected_header(
            lines: list[list[tuple[float, float, float, str]]],
    ) -> str | None:
        """Return the first line that looks like a column-header row.

        Only column labels are surfaced here (never transaction content), so
        the hint in error messages stays privacy-safe.
        """
        keywords = (
            "DATE", "VALUE", "PARTICULARS", "NARRATION", "DETAIL", "REF",
            "DEBIT", "DEPOSIT", "CREDIT", "WITHDRAWAL", "BALANCE", "CHQ",
            "AMOUNT", "TXNDATE", "TXN DATE", "TRANSACTION",
        )

        for line in lines:
            texts = " ".join(word[3] for word in line).upper()
            hits = sum(1 for keyword in keywords if keyword in texts)
            if hits >= 2:
                return " ".join(word[3] for word in line)

        return None

    @staticmethod
    def _is_header_line(
            line: list[tuple[float, float, float, str]],
    ) -> bool:
        texts = {word[3].upper() for word in line}
        has_date_word = any(
            token in texts for token in ("DATE", "POST", "VALUE")
        )
        has_details_word = any(
            token in texts
            for token in ("DETAILS", "NARRATION", "PARTICULARS", "DESCRIPTION")
        )
        return has_date_word and has_details_word

    @staticmethod
    def _skip_furniture(
            line: list[tuple[float, float, float, str]],
    ) -> bool:
        text = " ".join(word[3] for word in line).upper()
        return any(marker in text for marker in _FURNITURE_MARKERS)

    @staticmethod
    def _extract_date(
            line: list[tuple[float, float, float, str]],
            columns: dict[str, tuple[float, float]],
    ) -> str | None:
        for preferred in ("post_date", "value_date"):
            for word in line:
                if (
                    _column_for_word(columns, word) == preferred
                    and _DATE_PATTERN.match(word[3])
                ):
                    return word[3]
        return None

    @staticmethod
    def _is_summary_line(
            line: list[tuple[float, float, float, str]],
            columns: dict[str, tuple[float, float]],
    ) -> bool:
        has_debit = False
        has_credit = False

        for word in line:
            column = _column_for_word(columns, word)
            if column == "debit":
                has_debit = True
            elif column == "credit":
                has_credit = True

        return has_debit and has_credit

    @staticmethod
    def _append_line(
            current: dict[str, list[str]],
            line: list[tuple[float, float, float, str]],
            columns: dict[str, tuple[float, float]],
    ) -> None:
        for word in line:
            column = _column_for_word(columns, word)

            if column in ("details", "ref", "debit", "credit", "balance"):
                current[column].append(word[3])

    def _lines_to_transactions(
            self,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> list[dict[str, object]]:
        columns = self._header_columns(lines)

        if columns is None:
            header_hint = self._suspected_header(lines)
            hint = (
                f" Column-header row found: {header_hint!r}."
                if header_hint
                else " No column-header row was found (this may be a "
                "scanned/image-only PDF)."
            )
            raise ValueError(
                "Could not identify this as an SBI statement in this PDF."
                + hint
            )

        pending: list[dict[str, object]] = []
        current: dict[str, list[str]] | None = None

        for line in lines:
            if self._is_header_line(line) or self._skip_furniture(line):
                continue

            date_value = self._extract_date(line, columns)

            if date_value is not None:
                if current is not None:
                    pending.append(self._finalize_row(current))
                current = {
                    "date": [date_value],
                    "details": [],
                    "ref": [],
                    "debit": [],
                    "credit": [],
                    "balance": [],
                }

            if current is None:
                continue

            if self._is_summary_line(line, columns):
                continue

            self._append_line(current, line, columns)

        if current is not None:
            pending.append(self._finalize_row(current))

        return pending

    @staticmethod
    def _finalize_row(row: dict[str, list[str]]) -> dict[str, object]:
        return {
            "post_date": " ".join(row["date"]).strip(),
            "details": " ".join(row["details"]).strip(),
            "ref": " ".join(row["ref"]).strip(),
            "debit": " ".join(row["debit"]).strip(),
            "credit": " ".join(row["credit"]).strip(),
            "balance": " ".join(row["balance"]).strip(),
        }