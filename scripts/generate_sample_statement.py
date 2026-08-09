"""Generate the bundled sample statement shipped with KharchaLens.

Builds ``kharchalens/sample_data/sample_statement.xlsx`` — a realistic
ICICI-format statement spanning three months, so the dashboard's monthly
spending trend, highlights and average-monthly-spend are immediately visible.

Run from the repo root:
    uv run python scripts/generate_sample_statement.py
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

OUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "kharchalens"
    / "sample_data"
    / "sample_statement.xlsx"
)

BANNER = [
    ["DETAILED STATEMENT"],
    ["Account Number", "003401060110 ( INR )  - AAKASH  RAJ"],
    ["Search"],
    ["Transaction Date from", "01/06/2026", "to", "31/08/2026"],
    ["Transactions List - AAKASH RAJ - 003401060110"],
]

HEADERS = [
    "S No.",
    "Value Date",
    "Transaction Date",
    "Cheque Number",
    "Transaction Remarks",
    "Withdrawal Amount(INR)",
    "Deposit Amount(INR)",
    "Balance(INR)",
]

# (date, narration, withdrawal, deposit) — amounts as strings to mirror the
# ICICI export format. Deposit columns are empty strings on debits and vice
# versa. Running balance is computed from an opening amount below.
ROWS: list[tuple[date, str, str, str]] = [
    # ----- June 2026 -----
    (date(2026, 6, 1), "NEFT/CR/ICIC0000045/SALARY/JUNE 2026", "", "125000.00"),
    (date(2026, 6, 2), "UPI/SWIGGY/UPIPayment/ICICI Bank/110123456789", "640.00", ""),
    (date(2026, 6, 3), "UPI/ZOMATO/UPIPayment/ICICI Bank/110123456790", "890.00", ""),
    (date(2026, 6, 4), "UPI/AMAZON/UPIPayment/ICICI Bank/110123456791", "2499.00", ""),
    (date(2026, 6, 6), "MMT/IMPS/DEBIT/RENT/June 2026", "22000.00", ""),
    (date(2026, 6, 8), "UPI/BLINKIT/UPIPayment/ICICI Bank/110123456792", "1120.00", ""),
    (date(2026, 6, 12), "UPI/DMART/UPIPayment/ICICI Bank/110123456793", "3450.00", ""),
    (date(2026, 6, 15), "POS 5326 76XXXXXX 3401", "1800.00", ""),
    (date(2026, 6, 20), "UPI/IRCTC/UPIPayment/ICICI Bank/110123456794", "1750.00", ""),
    (date(2026, 6, 25), "UPI/NETFLIX/NFLXICICI/UPIPayment", "649.00", ""),
    (date(2026, 6, 28), "UPI/BESCOM/ELECTRICITY BILL/June 2026", "2840.00", ""),
    # ----- July 2026 -----
    (date(2026, 7, 1), "NEFT/CR/ICIC0000045/SALARY/JULY 2026", "", "125000.00"),
    (date(2026, 7, 2), "UPI/SWIGGY/UPIPayment/ICICI Bank/110123456795", "720.00", ""),
    (date(2026, 7, 5), "UPI/ZOMATO/UPIPayment/ICICI Bank/110123456796", "940.00", ""),
    (date(2026, 7, 7), "UPI/AMAZON/UPIPayment/ICICI Bank/110123456797", "1450.00", ""),
    (date(2026, 7, 8), "MMT/IMPS/DEBIT/RENT/July 2026", "22000.00", ""),
    (date(2026, 7, 11), "UPI/FLIPKART/UPIPayment/ICICI Bank/110123456798", "3200.00", ""),
    (date(2026, 7, 14), "POS 5326 76XXXXXX 3402", "5600.00", ""),
    (date(2026, 7, 18), "UPI/UBER/UPIPayment/ICICI Bank/110123456799", "245.00", ""),
    (date(2026, 7, 22), "NEFT/CR/UTI/DIVIDEND FY25-26", "", "5280.00"),
    (date(2026, 7, 26), "UPI/BESCOM/ELECTRICITY BILL/July 2026", "3150.00", ""),
    (date(2026, 7, 30), "UPI/MYNTRA/UPIPayment/ICICI Bank/110123456800", "1999.00", ""),
    # ----- August 2026 -----
    (date(2026, 8, 1), "NEFT/CR/ICIC0000045/SALARY/AUGUST 2026", "", "125000.00"),
    (date(2026, 8, 3), "UPI/SWIGGY/UPIPayment/ICICI Bank/110123456801", "830.00", ""),
    (date(2026, 8, 5), "UPI/BIGBASKET/BBNOW/UPIPayment", "1540.00", ""),
    (date(2026, 8, 7), "MMT/IMPS/DEBIT/RENT/Aug 2026", "22000.00", ""),
    (date(2026, 8, 10), "UPI/OLA/UPIPayment/ICICI Bank/110123456802", "310.00", ""),
    (date(2026, 8, 12), "POS 5326 76XXXXXX 3403", "2700.00", ""),
    (date(2026, 8, 15), "UPI/APOLLO PHARMACY/UPIPayment/ICICI Bank/110123456803", "860.00", ""),
    (date(2026, 8, 20), "UPI/JIO/UPIPayment/ICICI Bank/110123456804", "1299.00", ""),
    (date(2026, 8, 24), "UPI/UNKNOWN SHOP/UPIPayment/ICICI Bank/110123456805", "450.00", ""),
    (date(2026, 8, 27), "UPI/BESCOM/ELECTRICITY BILL/August 2026", "2980.00", ""),
]


def generate() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Statement"

    for row in BANNER:
        sheet.append(row)
    sheet.append(HEADERS)

    balance = Decimal("72000.00")

    for index, (day, narration, withdrawal, deposit) in enumerate(ROWS, start=1):
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

    sheet.append([
        "",
        "",
        "",
        "",
        "Sincerely,",
        "",
        "",
        "",
    ])
    sheet.append([
        "",
        "",
        "",
        "",
        "This is a system generated statement. ICICI Bank Ltd.",
        "",
        "",
        "",
    ])

    OUT_PATH.parent.mkdir(exist_ok=True)

    workbook.properties.creator = "KharchaLens"
    workbook.properties.lastModifiedBy = "KharchaLens"
    workbook.properties.created = datetime(2026, 1, 1)
    workbook.properties.modified = datetime(2026, 1, 1)

    workbook.save(OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    generate()