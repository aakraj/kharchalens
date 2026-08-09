from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from kharchalens.models import TransactionType
from kharchalens.parser import IciciParser

_HEADER = [
    "S No.",
    "Value Date",
    "Transaction Date",
    "Cheque Number",
    "Transaction Remarks",
    "Withdrawal Amount(INR)",
    "Deposit Amount(INR)",
    "Balance(INR)",
]


def _write_workbook(tmp_path, rows: list[list[object]]) -> str:
    df = pd.DataFrame(rows)
    path = tmp_path / "icici.xlsx"
    df.to_excel(path, header=False, index=False)
    return str(path)


def test_icici_excel_parses_real_layout(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            ["Account Number (INR) - SOMEBODY", "", ""],
            ["Transactions List - SOMEBODY", "", ""],
            [_HEADER[0], _HEADER[1], _HEADER[2], _HEADER[3], _HEADER[4],
             _HEADER[5], _HEADER[6], _HEADER[7]],
            ["1", "03/08/2026", "03/08/2026", "",
             "ACH/TP ACH INDIANESIGN/ICIC7021908241001264/2285633248",
             "5000.00", "0.00", "101318.84"],
            ["2", "04/08/2026", "04/08/2026", "1",
             "NEFT INB ICICIA AKAASH PATEL", "0.00", "2000.00", "103318.84"],
        ],
    )

    # The workbook has no "ICICI BANK" banner text; the header signature
    # (two date columns + remarks + amounts) is what gates it.
    transactions = IciciParser().parse(path)

    assert len(transactions) == 2

    debit = transactions[0]
    assert debit.date == date(2026, 8, 3)
    assert debit.transaction_type == TransactionType.DEBIT
    assert debit.amount == Decimal("5000.00")
    assert debit.balance == Decimal("101318.84")
    assert debit.reference_number is None

    credit = transactions[1]
    assert credit.date == date(2026, 8, 4)
    assert credit.transaction_type == TransactionType.CREDIT
    assert credit.amount == Decimal("2000.00")
    assert credit.balance == Decimal("103318.84")
    assert credit.reference_number == "1"


def test_icici_excel_rejects_single_date_sbi_header(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            ["State Bank of India", "", ""],
            ["Date", "Details", "Ref No/Cheque No", "Debit", "Credit", "Balance"],
            ["07/05/2025", "CEMTEX DEP ACHC", "0000000005629", "60.00", "", "75575.96"],
        ],
    )

    with pytest.raises(ValueError, match="transaction table"):
        IciciParser().parse(path)


def test_icici_excel_requires_header_row(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            ["Transactions List - SOMEONE", "", ""],
            ["1", "03/08/2026", "03/08/2026", "",
             "NEFT", "5000.00", "0.00", "101318.84"],
        ],
    )

    with pytest.raises(ValueError, match="transaction table"):
        IciciParser().parse(path)