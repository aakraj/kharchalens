from __future__ import annotations

import re
import statistics
import traceback
from collections.abc import Callable

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
    "STATEMENT FROM",
    "PAGE NO",
    "PAGE",
    "YOUR ACCOUNT",
    "BALANCE CARRIED",
    "TRANSACTIONS AS ON",
    "OPENING BALANCE",
    "CLEAR BALANCE",
    "UNCLEARED",
    "CLOSING BALANCE",
    "FORWARD",
    "OVERDRAWN",
    "DEBITS(",
    "DEBITS (",
    "CREDITS(",
    "CREDITS (",
    "DEBIT SUMMARY",
    "CREDIT SUMMARY",
    "PLEASE DO NOT SHARE",
    "POWER OF ATTORNEY",
    "IF YOUR ACCOUNT",
    "TRANSACTIONS WITH EXTRA",
    "THANK YOU",
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
        """Return the first few lines that look like a column header.

        Only rows that carry at least two column-like labels are surfaced, so
        the hint stays privacy-safe and skips ordinary transaction rows.
        """
        keywords = (
            "DATE", "VALUE", "PARTICULARS", "NARRATION", "DETAIL", "REF",
            "DEBIT", "DEPOSIT", "CREDIT", "WITHDRAWAL", "BALANCE", "CHQ",
            "AMOUNT",
        )

        found: list[str] = []

        for line in lines:
            words = [(word[3], round(word[0])) for word in line]
            text = " ".join(word for word, _ in words).upper()

            hits = sum(1 for token in keywords if token in text)
            if hits >= 2:
                found.append(
                    " ".join(f"{word}@{x}" for word, x in words)
                )
            if len(found) >= 4:
                break

        return "  ||  ".join(found) or None

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
            classify: Callable[[tuple[float, float, float, str]], str | None],
    ) -> str | None:
        for preferred in ("post_date", "value_date"):
            for word in line:
                if (
                    classify(word) == preferred
                    and _DATE_PATTERN.match(word[3])
                ):
                    return word[3]
        return None

    @staticmethod
    def _is_summary_line(
            line: list[tuple[float, float, float, str]],
            classify: Callable[[tuple[float, float, float, str]], str | None],
    ) -> bool:
        has_debit = False
        has_credit = False

        for word in line:
            column = classify(word)
            if column == "debit":
                has_debit = True
            elif column == "credit":
                has_credit = True

        return has_debit and has_credit

    @staticmethod
    def _append_line(
            current: dict[str, list[str]],
            line: list[tuple[float, float, float, str]],
            classify: Callable[[tuple[float, float, float, str]], str | None],
    ) -> None:
        for word in line:
            column = classify(word)
            if column is None:
                continue
            if column in ("details", "ref", "debit", "credit", "balance"):
                current[column].append(word[3])

    @classmethod
    def _geometric_columns(
            cls,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> dict[str, float] | None:
        """Infer column positions from geometry when no header row exists.

        SBI e-statements whose transaction table lacks a column-header row
        (all figures are right-aligned per column) are still parseable: they
        consistently place two date columns, a particulars column, and three
        numeric bands (debit, credit, balance) at stable x-coordinates. All
        revenue/monetary tokens sit on the same line as a dd/mm/yyyy date.
        """
        date_lines = [
            line
            for line in lines
            if any(_DATE_PATTERN.match(word[3]) for word in line)
        ]
        if not date_lines:
            return None

        date_xs = sorted({
            word[0]
            for line in date_lines
            for word in line
            if _DATE_PATTERN.match(word[3])
        })
        if not date_xs:
            return None
        post_date = date_xs[0]
        value_date = date_xs[1] if len(date_xs) > 1 else date_xs[0]

        text_xs = [
            word[0]
            for line in date_lines
            for word in line
            if (
                not _DATE_PATTERN.match(word[3])
                and not _NUMERIC_PATTERN.match(word[3])
                and word[3] != "-"
            )
        ]
        details_x = statistics.median(text_xs) if text_xs else None

        numeric_xs = sorted(
            word[0]
            for line in date_lines
            for word in line
            if _NUMERIC_PATTERN.match(word[3])
        )

        bands: list[list[float]] = []
        for x in numeric_xs:
            if bands and x - bands[-1][-1] <= 20:
                bands[-1].append(x)
            else:
                bands.append([x])

        centres = [statistics.median(band) for band in bands]

        if len(centres) < 2:
            return None

        balance = centres[-1]
        debit = centres[0]
        credit = centres[1] if len(centres) > 2 else None

        # Narration words live to the right of the (second) date column and
        # left of the first amount column.
        value_tail = value_date + 3
        amount_head = debit - 40
        details_xs = [
            word[0]
            for line in date_lines
            for word in line
            if (value_tail < word[0] < amount_head)
        ]
        if not details_xs:
            details_xs = list(text_xs)
        details_x = statistics.median(details_xs) if details_xs else 0.0

        return {
            "post_date": post_date,
            "value_date": value_date,
            "details": details_x,
            "debit": debit,
            "credit": credit or balance,
            "balance": balance,
        }

    @staticmethod
    def _classify_geometric(
            word: tuple[float, float, float, str],
            columns: dict[str, float],
    ) -> str | None:
        text = word[3]
        centre = (word[0] + word[1]) / 2

        if _DATE_PATTERN.match(text):
            if abs(centre - columns["value_date"]) < abs(
                centre - columns["post_date"]
            ):
                return "value_date"
            return "post_date"

        if text == "-":
            return None

        if _NUMERIC_PATTERN.match(text):
            return min(
                ("details", "debit", "credit", "balance"),
                key=lambda key: abs(centre - columns[key]),
            )

        return "details"

    def _lines_to_transactions(
            self,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> list[dict[str, object]]:
        header_columns = self._header_columns(lines)

        if header_columns is not None:
            classify: Callable[
                [tuple[float, float, float, str]], str | None
            ] = lambda word: _column_for_word(header_columns, word)
            is_header = self._is_header_line
            narration_before = False
        else:
            geometric = self._geometric_columns(lines)

            if geometric is None:
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

            classify = lambda word: self._classify_geometric(word, geometric)
            is_header = lambda line: False
            narration_before = True

        pending: list[dict[str, object]] = []
        current: dict[str, list[str]] | None = None
        narration: list[str] = []

        for line in lines:
            if is_header(line) or self._skip_furniture(line):
                narration.clear()
                continue

            date_value = self._extract_date(line, classify)

            if date_value is not None:
                if current is not None:
                    pending.append(self._finalize_row(current))

                current = {
                    "date": [date_value],
                    "details": narration if narration_before else [],
                    "ref": [],
                    "debit": [],
                    "credit": [],
                    "balance": [],
                }
                narration = []

                if self._is_summary_line(line, classify):
                    continue
                self._append_line(current, line, classify)
                continue

            if narration_before:
                for word in line:
                    column = classify(word)
                    if column in ("details", "ref"):
                        narration.append(word[3])
                continue

            if current is None:
                continue

            if self._is_summary_line(line, classify):
                continue

            self._append_line(current, line, classify)

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