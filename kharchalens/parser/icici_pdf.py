from __future__ import annotations

import re
import statistics

from .icici_base import IciciStatementParser
from .sbi_pdf import SbiPdfParser

_DATE_PATTERN = re.compile(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$")

_NUMERIC_PATTERN = re.compile(r"^₹?[\d,]+(?:\.\d+)?$")

_ICICI_FURNITURE_MARKERS = (
    "SINCERELY",
    "TEAM ICICI BANK",
    "SYSTEM GENERATED",
    "WWW.ICICI",
    "DIAL YOUR BANK",
    "PLEASE CALL FROM YOUR REGISTERED",
    "NEVER SHARE YOUR OTP",
    "LEGENDS FOR TRANSACTIONS",
    "SMO - SMART MONEY ORDER",
    "PAVC - PAY",
    "DTAX - DIRECT TAX",
    "VPS/IPS",
    "PAC - PERSONAL",
    "BPAY - BILL",
    "TOP - MOBILE",
    "LNPY - LINKED LOAN",
    "IDTX - INDIRECT TAX",
    "BCTT - BANKING CASH",
    "CCWD - CARDLESS",
    "BBPS - BHARAT BILL",
    "UCCBRN CMS",
    "LCCBRN CMS",
    "PAYC - PAY TO",
    "INFT - INTERNAL FUND",
    "IMPS - IMMEDIATE",
    "BIL - INTERNET BILL",
    "NCHG - NEFT CHARGES",
    "VAT/MAT/NFS",
    "ONL - ONLINE",
    "MMT - MOBILE MONEY",
    "MMT - MOBILE MONEY TRANSFER",
    "INF - INTERNET FUND",
    "NEFT - NATIONAL ELECTRONIC",
    "T CHG - TRAVEL",
    "EBA - TRANSACTION ON ICICI DIRECT",
    "SGB - SOVEREIGN GOLD BOND",
    "SINCERLY",
)

_END_OF_STATEMENT_MARKERS = (
    "SINCERLY, TEAM ICICI BANK",
    "LEGENDS FOR TRANSACTIONS",
    "THIS IS A SYSTEM GENERATED STATEMENT",
    "WWW.ICICI.BANK.IN",
)


class IciciPdfParser(SbiPdfParser, IciciStatementParser):
    """Parses ICICI statement PDFs using word positions and geometry.

    ICICI e-statement PDFs carry a fixed table (S.No., dot-formatted
    transaction date, narration lines below each row, right-aligned
    Withdrawal / Deposit / Balance amounts). There is no usable one-line
    column header and the narration is not always on the dated row, so the
    columns are inferred geometrically from the dated rows' amount
    positions. Only files that mention ``ICICI Bank`` are claimed.
    """

    def _lines_to_transactions(
            self,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> list[dict[str, object]]:
        if not self._looks_like_icici_pdf(lines):
            raise ValueError(
                "Could not identify this as an ICICI statement in this PDF."
            )

        columns = self._geometric_columns(lines)

        if columns is None:
            raise ValueError(
                "Could not identify the ICICI statement columns in this PDF."
            )

        pending: list[dict[str, list[str]]] = []
        current: dict[str, list[str]] | None = None

        for line in lines:
            if self._skip_furniture(line):
                if self._is_end_of_statement(line):
                    break
                continue

            date_value = self._extract_date_text(line)

            if date_value is not None:
                if current is not None:
                    pending.append(current)
                    current = None

                current = {
                    "post_date": [date_value],
                    "value_date": [],
                    "details": [],
                    "ref": [],
                    "debit": [],
                    "credit": [],
                    "balance": [],
                }
                self._append_amounts(current, line, columns)
                continue

            if current is None:
                continue

            for word in line:
                column = self._classify_icici(word, columns)
                if column == "details":
                    current["details"].append(word[3])
                elif column == "ref":
                    current["ref"].append(word[3])

        if current is not None:
            pending.append(current)

        rows = [self._finalize_row(row) for row in pending]
        self._strip_next_row_orphans(rows)
        return rows

    @staticmethod
    def _strip_next_row_orphans(
            rows: list[dict[str, object]],
    ) -> None:
        """Remove trailing narration words that actually belong to the next
        row. ICICI PDFs place an orphan name/fragment line (e.g. a repeated
        merchant or beneficiary name) just above the next date row; these
        words are always a substring of the following row's own narration.
        """
        for index in range(len(rows)):
            if index == len(rows) - 1:
                break

            details = str(rows[index]["details"]).strip()
            following = str(rows[index + 1]["details"]).upper()

            if not details or not following:
                continue

            words = details.split()
            trailing: list[str] = []

            for word in reversed(words):
                if not word.isalpha():
                    break
                if word.upper() not in following:
                    break
                trailing.append(word)

            if trailing:
                trim = len(trailing)
                if trim < len(words):
                    rows[index]["details"] = " ".join(words[: -trim])
                else:
                    rows[index]["details"] = ""

    @staticmethod
    def _skip_furniture(
            line: list[tuple[float, float, float, str]],
    ) -> bool:
        text = " ".join(word[3] for word in line).upper()
        if SbiPdfParser._skip_furniture(line):
            return True
        return any(marker in text for marker in _ICICI_FURNITURE_MARKERS)

    @staticmethod
    def _is_end_of_statement(
            line: list[tuple[float, float, float, str]],
    ) -> bool:
        text = " ".join(word[3] for word in line).upper()
        return any(marker in text for marker in _END_OF_STATEMENT_MARKERS)

    @staticmethod
    def _extract_date_text(
            line: list[tuple[float, float, float, str]],
    ) -> str | None:
        for word in line:
            if _DATE_PATTERN.match(word[3]):
                return word[3]
        return None

    @classmethod
    def _geometric_columns(
            cls,
            lines: list[list[tuple[float, float, float, str]]],
    ) -> dict[str, float] | None:
        date_lines = [
            line
            for line in lines
            if any(_DATE_PATTERN.match(word[3]) for word in line)
        ]
        if not date_lines:
            return None

        date_xs = [
            word[0]
            for line in date_lines
            for word in line
            if _DATE_PATTERN.match(word[3])
        ]
        post_date = statistics.median(date_xs)

        # Amounts are right-aligned, so cluster by right edge (x1), ignoring
        # the row-level serial number and any words left of the date column.
        numeric_x1s = sorted(
            word[1]
            for line in date_lines
            for word in line
            if _NUMERIC_PATTERN.match(word[3]) and word[0] > post_date + 10
        )
        if not numeric_x1s:
            return None

        bands: list[list[float]] = []
        for x in numeric_x1s:
            if bands and x - bands[-1][-1] <= 5.0:
                bands[-1].append(x)
            else:
                bands.append([x])

        centres = [statistics.median(band) for band in bands]
        balance = centres[-1]
        amounts = centres[:-1]

        if len(amounts) == 0:
            return None

        debit = amounts[0]
        credit = amounts[1] if len(amounts) > 1 else debit

        return {
            "post_date": post_date,
            "debit": debit,
            "credit": credit,
            "balance": balance,
        }

    @staticmethod
    def _classify_icici(
            word: tuple[float, float, float, str],
            columns: dict[str, float],
    ) -> str | None:
        text = word[3]

        if _DATE_PATTERN.match(text):
            return "post_date"

        if _NUMERIC_PATTERN.match(text):
            if word[0] < columns["post_date"] + 20.0:
                return None
            key = min(
                ("debit", "credit", "balance"),
                key=lambda k: abs(word[1] - columns[k]),
            )
            near_amounts = abs(word[1] - columns[key])
            if near_amounts > 40.0:
                return "details"
            return key if key in ("debit", "credit") else "balance"

        return "details"

    @staticmethod
    def _append_amounts(
            current: dict[str, list[str]],
            line: list[tuple[float, float, float, str]],
            columns: dict[str, float],
    ) -> None:
        for word in line:
            column = IciciPdfParser._classify_icici(word, columns)
            if column == "debit":
                current["debit"].append(word[3])
            elif column == "credit":
                current["credit"].append(word[3])
            elif column == "balance":
                current["balance"].append(word[3])

    @staticmethod
    def _finalize_row(row: dict[str, list[str]]) -> dict[str, object]:
        return {
            "post_date": " ".join(row["post_date"]).strip(),
            "details": " ".join(row["details"]).strip(),
            "ref": " ".join(row["ref"]).strip(),
            "debit": " ".join(row["debit"]).strip(),
            "credit": " ".join(row["credit"]).strip(),
            "balance": " ".join(row["balance"]).strip(),
        }

    @staticmethod
    def _looks_like_icici_pdf(
            lines: list[list[tuple[float, float, float, str]]],
    ) -> bool:
        for line in lines:
            text = " ".join(word[3] for word in line).upper()
            if "ICICI BANK" in text:
                return True
        return False