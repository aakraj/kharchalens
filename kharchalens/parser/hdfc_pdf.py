from __future__ import annotations

import re
import traceback
from dataclasses import dataclass, field
from typing import cast

import pdfplumber

from kharchalens.models import Transaction

from .hdfc_base import HdfcStatementParser

_DATE_PATTERN = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")

_NUMERIC_PATTERN = re.compile(r"^₹?[\d,]+(?:\.\d+)?$")

_TRIGGER_WORDS = {
    "date": "DATE",
    "narration": "NARRATION",
    "ref": "CHQ",
    "value": "VALUE",
    "withdrawal": "WITHDRAWAL",
    "deposit": "DEPOSIT",
    "closing": "CLOSING",
}

_FURNITURE_MARKERS = (
    "HDFC BANK",
    "PAGE NO",
    "STATEMENT OF ACCOUNT",
    "NOMINATION",
    "CLOSING BALANCE INCLUDES",
    "DOWNLOAD TO READ",
    "WE UNDERSTAND YOUR WORLD",
)


class PdfPasswordRequired(ValueError):
    """The statement PDF is encrypted and no password was supplied."""


class PdfIncorrectPassword(ValueError):
    """The supplied password did not decrypt the statement PDF."""


@dataclass(slots=True)
class _PendingRow:
    date: str
    narration: list[str] = field(default_factory=list)
    reference: list[str] = field(default_factory=list)
    withdrawal: list[str] = field(default_factory=list)
    deposit: list[str] = field(default_factory=list)
    closing: list[str] = field(default_factory=list)


class HdfcPdfParser(HdfcStatementParser):
    """Parses HDFC NetBanking statement PDFs using word positions.

    HDFC PDFs are text-based but blank withdrawal/deposit cells simply
    disappear from the raw text, so values are assigned to columns by
    their x-coordinate relative to the repeated table header row.
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
                    lines.extend(self._group_words_by_line(words))

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

    @staticmethod
    def _group_words_by_line(
            words: list[dict[str, object]],
    ) -> list[list[tuple[float, float, float, str]]]:
        grouped: dict[float, list[tuple[float, float, float, str]]] = {}

        for word in words:
            top = float(cast(float, word["top"]))
            key = round(top, 1)
            grouped.setdefault(key, []).append(
                (cast(float, word["x0"]), cast(float, word["x1"]), top, cast(str, word["text"]))
            )

        lines: list[list[tuple[float, float, float, str]]] = []

        for key in sorted(grouped):
            lines.append(sorted(grouped[key], key=lambda item: item[0]))

        return lines

    def _lines_to_transactions(
            self,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> list[dict[str, object]]:
        columns = self._header_columns(lines)

        if columns is None:
            raise ValueError(
                "Could not identify the HDFC statement table in this PDF."
            )

        pending: list[_PendingRow] = []
        current: _PendingRow | None = None
        # ``carried`` is the last row of the previous page, kept alive so that
        # continuation lines of a multi-line narration which physically spill
        # onto the next page can still be appended to it.
        carried: _PendingRow | None = None
        last_top: float | None = None

        for line in lines:
            if self._is_header_line(line):
                continue

            if self._skip_furniture(line):
                continue

            top = line[0][2]

            # Each HDFC page carries its own account-info header block above
            # the transaction table. Within a page ``top`` only increases, so
            # a drop back to near the top of the page marks the start of the
            # next page. Finalise the previous page's last row here, and do
            # not let that account-info block leak into it. ``carried`` keeps
            # that row addressable for any narration continuing on this page.
            if (
                current is not None
                and last_top is not None
                and top < last_top - 20.0
            ):
                pending.append(current)
                carried = current
                current = None

            last_top = top

            date_value = self._extract_date(line, columns)

            if date_value is not None:
                if current is not None:
                    pending.append(current)
                current = _PendingRow(date=date_value)
                carried = None

            if current is None:
                if (
                    carried is not None
                    and self._is_data_continuation(line, columns)
                    and not self._is_summary_line(line, columns)
                ):
                    self._append_line(carried, line, columns)
                continue

            if self._is_summary_line(line, columns):
                continue

            self._append_line(current, line, columns)

        if current is not None:
            pending.append(current)

        return [self._finalize_row(row) for row in pending]

    def _header_columns(
            self,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> dict[str, tuple[float, float]] | None:
        for line in lines:
            texts = {word[3].upper() for word in line}

            if not (
                "DATE" in texts
                and "NARRATION" in texts
            ):
                continue

            centers: dict[str, tuple[float, float]] = {}

            for key, trigger in _TRIGGER_WORDS.items():
                for word in line:
                    if word[3].upper().startswith(trigger):
                        centers[key] = (word[0], word[1])
                        break

            if len(centers) != len(_TRIGGER_WORDS):
                continue

            return centers

        return None

    @staticmethod
    def _is_data_continuation(
            line: list[tuple[float, float, float, str]],
            columns: dict[str, tuple[float, float]],
    ) -> bool:
        """True for a narration continuation line, not page furniture.

        Applied to a row carried across a page boundary: a real continuation
        line holds only narration/ref words, whereas the repeating account-
        info block above the table also carries left-margin (date) and
        value/amount words.
        """
        for word in line:
            if _column_for_word(columns, word) not in {"narration", "ref"}:
                return False
        return bool(line)

    @staticmethod
    def _is_header_line(
            line: list[tuple[float, float, float, str]],
    ) -> bool:
        texts = {word[3].upper() for word in line}
        return "DATE" in texts and "NARRATION" in texts

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
        for word in line:
            if _column_for_word(columns, word) == "date" and _DATE_PATTERN.match(word[3]):
                return word[3]

        return None

    @staticmethod
    def _is_summary_line(
            line: list[tuple[float, float, float, str]],
            columns: dict[str, tuple[float, float]],
    ) -> bool:
        """True for a grand-total/summary row filling both amount columns.

        A real HDFC transaction populates either the withdrawal or the
        deposit cell, never both. A closing totals row (end of statement / end
        of page) fills both, so it must not be folded into the last row.
        """
        has_withdrawal = False
        has_deposit = False

        for word in line:
            column = _column_for_word(columns, word)
            if column == "withdrawal":
                has_withdrawal = True
            elif column == "deposit":
                has_deposit = True

        return has_withdrawal and has_deposit

    @staticmethod
    def _append_line(
            current: _PendingRow,
            line: list[tuple[float, float, float, str]],
            columns: dict[str, tuple[float, float]],
    ) -> None:
        for word in line:
            column = _column_for_word(columns, word)

            if column == "narration":
                current.narration.append(word[3])
            elif column == "ref":
                current.reference.append(word[3])
            elif column == "withdrawal":
                current.withdrawal.append(word[3])
            elif column == "deposit":
                current.deposit.append(word[3])
            elif column == "closing":
                current.closing.append(word[3])

    @staticmethod
    def _finalize_row(row: _PendingRow) -> dict[str, object]:
        return {
            "Date": row.date,
            "Narration": " ".join(row.narration).strip(),
            "Chq./Ref.No.": " ".join(row.reference).strip(),
            "Withdrawal Amt.": " ".join(row.withdrawal).strip(),
            "Deposit Amt.": " ".join(row.deposit).strip(),
            "Closing Balance": " ".join(row.closing).strip(),
        }


def _column_for_word(
        columns: dict[str, tuple[float, float]],
        word: tuple[float, float, float, str],
) -> str:
    anchor = word[1] if _NUMERIC_PATTERN.match(word[3]) else word[0]

    ordered = sorted(columns.items(), key=lambda item: item[1][0])

    # The date column is narrow: it ends at the "Date" header word's right
    # edge, and narration data starts there. Every other column starts at its
    # own header word's left edge. In real HDFC PDFs the "Narration" header
    # label sits far right of where narration text actually begins.
    bounds: dict[str, float] = {ordered[0][0]: 0.0}

    if len(ordered) > 1:
        bounds[ordered[1][0]] = ordered[0][1][1]

    for key, (left, _right) in ordered[2:]:
        bounds[key] = left

    column = ordered[0][0]

    for key, (_left, _right) in ordered:
        if anchor < bounds[key]:
            break
        column = key

    return column
