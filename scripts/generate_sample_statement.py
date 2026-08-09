"""Generate the bundled sample statements shipped with KharchaLens.

Builds two realistic statements spanning twelve months (Sep 2025 – Aug 2026),
so the dashboard's monthly spending trend, highlights and average-monthly-
spend are immediately visible:

* ``kharchalens/sample_data/sample_statement_icici.xlsx`` (ICICI format)
* ``kharchalens/sample_data/sample_statement_hdfc.xlsx``   (HDFC format)

Both files are derived from the same transaction plan below.

Run from the repo root:
    uv run python scripts/generate_sample_statement.py
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

SAMPLE_DIR = (
    Path(__file__).resolve().parent.parent
    / "kharchalens"
    / "sample_data"
)

ICICI_OUT = SAMPLE_DIR / "sample_statement_icici.xlsx"
HDFC_OUT = SAMPLE_DIR / "sample_statement_hdfc.xlsx"

START_YEAR = 2025
START_MONTH = 9  # Sep 2025 … Aug 2026 (12 months)

# A monthly transaction plan. Each entry is
#   (day, narration, withdrawal, deposit)
# amounts are strings to mirror bank-export formatting; empty string means
# no amount in that column. Narrations embed merchant keywords on purpose so
# the dashboard's merchant detection is immediately visible.
MONTHLY_PLAN: list[tuple[int, str, str, str]] = [
    # Salary lands on the 1st.
    (1, "NEFT/CR/ICIC0000045/SALARY/MMM YYYY", "", "125000.00"),
    # Recurring spends.
    (2, "UPI/SWIGGY/UPIPayment/ICICI Bank", "745.00", ""),
    (3, "UPI/ZOMATO/UPIPayment/ICICI Bank", "898.00", ""),
    (6, "UPI/MFUTIL/UPIPayment/ICICI Bank", "5000.00", ""),
    (8, "UPI/BLINKIT/UPIPayment/ICICI Bank", "1140.00", ""),
    (10, "UPI/BESCOM/ELECTRICITY BILL/Current month", "2870.00", ""),
    (12, "UPI/DMART/UPIPayment/ICICI Bank", "3480.00", ""),
    (15, "POS 5326 76XXXXXX 3401", "1890.00", ""),
    (16, "UPI/ZERODHA/UPIPayment/ICICI Bank", "4500.00", ""),
    (18, "UPI/UBER/UPIPayment/ICICI Bank", "240.00", ""),
    (20, "UPI/IRCTC/UPIPayment/ICICI Bank", "1620.00", ""),
    (22, "UPI/NETFLIX/NFLXICICI/UPIPayment", "649.00", ""),
    (25, "UPI/SPOTIFY/UPIPayment/ICICI Bank", "149.00", ""),
    (26, "UPI/AMAZON/UPIPayment/ICICI Bank", "1850.00", ""),
    (28, "UPI/FLIPKART/UPIPayment/ICICI Bank", "2240.00", ""),
]

# (day, narration, withdrawal) — monthly debits not on the fixed plan.
MONTHLY_EXTRA: list[tuple[int, str, str]] = [
    (4, "UPI/UNKNOWN SHOP/UPIPayment/ICICI Bank", "425.00"),
    (11, "UPI/PETROL/UPIPayment/ICICI Bank", "2000.00"),
    (17, "UPI/OLA/UPIPayment/ICICI Bank", "310.00"),
]

# (month_number 1-12, narration, deposit) — recurring credits on top of salary.
QUARTERLY_CREDITS: list[tuple[int, str, str]] = [
    (1, "NEFT/CR/UTI/DIVIDEND FY25-26", "5280.00"),
    (4, "NEFT/CR/UTI/DIVIDEND FY25-26", "5420.00"),
    (7, "NEFT/CR/UTI/DIVIDEND FY25-26", "5310.00"),
    (10, "NEFT/CR/UTI/DIVIDEND FY25-26", "5560.00"),
]

# (month_number 1-12, narration, withdrawal, deposit)
OCCASIONAL: list[tuple[int, str, str, str]] = [
    (3, "UPI/APOLLO PHARMACY/UPIPayment/ICICI Bank", "845.00", ""),
    (3, "UPI/MYNTRA/UPIPayment/ICICI Bank", "1890.00", ""),
    (5, "UPI/FLIPKART/UPIPayment/ICICI Bank", "4699.00", ""),
    (6, "UPI/JIO/UPIPayment/ICICI Bank", "1299.00", ""),
    (6, "UPI/BIGBASKET/BBNOW/UPIPayment", "1510.00", ""),
    (8, "UPI/MYNTRA/UPIPayment/ICICI Bank", "2199.00", ""),
    (9, "UPI/APOLLO PHARMACY/UPIPayment/ICICI Bank", "720.00", ""),
    (10, "UPI/JIO/UPIPayment/ICICI Bank", "1499.00", ""),
    (11, "UPI/BIGBASKET/BBNOW/UPIPayment", "1280.00", ""),
    (12, "UPI/FLIPKART/UPIPayment/ICICI Bank", "7200.00", ""),
]


def _month_year(month_index: int) -> tuple[int, int]:
    """Map a 0-based month index to (year, month)."""
    year = START_YEAR + (START_MONTH - 1 + month_index) // 12
    month = (START_MONTH - 1 + month_index) % 12 + 1
    return year, month


def _month_label(month_index: int) -> str:
    year, month = _month_year(month_index)
    return date(year, month, 1).strftime("%B %Y").upper()


def _day_last(month_index: int) -> int:
    """The last day of the month for a 0-based month index."""
    from calendar import monthrange

    year, month = _month_year(month_index)
    return monthrange(year, month)[1]


def _transactions() -> list[tuple[date, str, str, str]]:
    """Build the full 12-month (date, narration, withdrawal, deposit) list."""
    rows: list[tuple[date, str, str, str]] = []

    for month_index in range(12):
        year, month = _month_year(month_index)
        label = _month_label(month_index)

        for day, narration, withdrawal, deposit in MONTHLY_PLAN:
            rows.append(
                (
                    date(year, month, day),
                    narration.replace("MMM YYYY", label),
                    withdrawal,
                    deposit,
                )
            )

        for day, narration, withdrawal in MONTHLY_EXTRA:
            rows.append((date(year, month, day), narration, withdrawal, ""))

        month_number = month_index + 1
        for month_number_, narration, deposit in QUARTERLY_CREDITS:
            if month_number == month_number_:
                rows.append(
                    (date(year, month, 22), narration, "", deposit)
                )

        for month_number_, narration, withdrawal, deposit in OCCASIONAL:
            if month_number == month_number_:
                rows.append(
                    (date(year, month, _day_last(month_index)), narration, withdrawal, deposit)
                )

    return sorted(rows, key=lambda row: (row[0], row[1]))


def _write_icici(rows: list[tuple[date, str, str, str]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Statement"

    banner = [
        ["DETAILED STATEMENT"],
        ["Account Number", "003401060110 ( INR )  - AAKASH  RAJ"],
        ["Search"],
        ["Transaction Date from", "01/09/2025", "to", "31/08/2026"],
        ["Transactions List - AAKASH RAJ - 003401060110"],
    ]
    headers = [
        "S No.",
        "Value Date",
        "Transaction Date",
        "Cheque Number",
        "Transaction Remarks",
        "Withdrawal Amount(INR)",
        "Deposit Amount(INR)",
        "Balance(INR)",
    ]

    for row in banner:
        sheet.append(row)
    sheet.append(headers)

    balance = Decimal("72000.00")

    for index, (day, narration, withdrawal, deposit) in enumerate(rows, start=1):
        amount = Decimal(withdrawal or deposit or "0.00")
        balance = balance - amount if withdrawal else balance + amount

        sheet.append([
            index,
            day.strftime("%d/%m/%Y"),
            day.strftime("%d/%m/%Y"),
            "",
            narration,
            withdrawal or "0.00",
            deposit or "0.00",
            f"{balance:.2f}",
        ])

    sheet.append(["", "", "", "", "Sincerely,", "", "", ""])
    sheet.append(
        ["", "", "", "", "This is a system generated statement. ICICI Bank Ltd.", "", "", ""]
    )

    workbook.properties.creator = "KharchaLens"
    workbook.properties.lastModifiedBy = "KharchaLens"
    workbook.properties.created = datetime(2026, 1, 1)
    workbook.properties.modified = datetime(2026, 1, 1)

    workbook.save(ICICI_OUT)


def _write_hdfc(rows: list[tuple[date, str, str, str]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Statement"

    banner = [
        ["HDFC BANK Ltd.                                      Page No .:   1"],
        ["Statement of accounts"],
        ["Account Branch :IT PARK"],
        ["MR.     AAKASH RAJ"],
        ["A-405, VS SAI ASHRAYA, BELATHUR MAIN ROAD, KADUGODI POST"],
        ["BIDARAHALLI HOBLI, BANGALORE 560067"],
    ]
    headers = [
        "Date",
        "Narration",
        "Chq./Ref.No.",
        "Value Dt",
        "Withdrawal Amt.",
        "Deposit Amt.",
        "Closing Balance",
    ]

    for row in banner:
        sheet.append(row)
    sheet.append(headers)
    # Masked-characters privacy row HDFC puts right under the header.
    sheet.append(["********", "**********************************", "************",
                  "********", "******************", "******************",
                  "******************"])

    balance = Decimal("72000.00")

    for day, narration, withdrawal, deposit in rows:
        amount = Decimal(withdrawal or deposit or "0.00")
        balance = balance - amount if withdrawal else balance + amount

        sheet.append([
            day.strftime("%d/%m/%y"),
            narration,
            "",
            day.strftime("%d/%m/%y"),
            withdrawal or "",
            deposit or "",
            f"{balance:.2f}",
        ])

    sheet.append([""])
    sheet.append(["Sincerely,"])
    sheet.append(["This is a computer generated statement. HDFC Bank Ltd."])

    workbook.properties.creator = "KharchaLens"
    workbook.properties.lastModifiedBy = "KharchaLens"
    workbook.properties.created = datetime(2026, 1, 1)
    workbook.properties.modified = datetime(2026, 1, 1)

    workbook.save(HDFC_OUT)


def generate() -> None:
    rows = _transactions()
    SAMPLE_DIR.mkdir(exist_ok=True)
    _write_icici(rows)
    _write_hdfc(rows)
    print(f"Wrote {ICICI_OUT} ({len(rows)} transactions)")
    print(f"Wrote {HDFC_OUT} ({len(rows)} transactions)")


if __name__ == "__main__":
    generate()
