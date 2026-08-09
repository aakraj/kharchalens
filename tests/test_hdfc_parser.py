from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from kharchalens.models import TransactionType
from kharchalens.parser import HdfcParser

_HEADER = [
    "Date",
    "Narration",
    "Chq./Ref.No.",
    "Value Dt",
    "Withdrawal Amt.",
    "Deposit Amt.",
    "Closing Balance",
]


def _write_workbook(tmp_path, rows: list[list[object]]) -> str:
    df = pd.DataFrame(rows)
    path = tmp_path / "hdfc.xlsx"
    df.to_excel(path, header=False, index=False)
    return str(path)


def test_hdfc_excel_parses_real_layout(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            ["Account No: 50100234567890", "", "", "", "", "", ""],
            ["Statement Period: 01/09/2025 - 30/09/2025", "", "", "", "", "", ""],
            [_HEADER[0], _HEADER[1], _HEADER[2], _HEADER[3],
             _HEADER[4], _HEADER[5], _HEADER[6]],
            ["05/09/25", "UPI/P2A/123456789012/DURGAPRASAD", "4237986510",
             "05/09/25", "1,200.00", "", "22,300.00"],
            ["01/09/25", "SWIGGY 123456789012", "", "01/09/25",
             "", "450.00", "23,500.00"],
            ["06/09/25", "NEFT/CR/NARENDRAMODI", "", "06/09/25",
             "", "25,000.00", "47,300.00"],
        ]
    )
    transactions = HdfcParser().parse(path)

    assert len(transactions) == 3

    debit, credit, neft = transactions
    assert debit.date == date(2025, 9, 5)
    assert debit.transaction_type == TransactionType.DEBIT
    assert debit.amount == Decimal("1200.00")
    assert debit.balance == Decimal("22300.00")
    assert debit.reference_number == "4237986510"
    assert "DURGAPRASAD" in debit.narration

    assert credit.date == date(2025, 9, 1)
    assert credit.transaction_type == TransactionType.CREDIT
    assert credit.amount == Decimal("450.00")

    assert neft.transaction_type == TransactionType.CREDIT
    assert neft.amount == Decimal("25000.00")


def test_header_found_above_masked_rows(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            ["Account No: 50100234567890", "", "", "", "", "", ""],
            list(_HEADER),
            ["01/09/25", "UPI/P2A/123456789012/DURGAPRASAD", "4237986510",
             "01/09/25", "1,200.00", "", "22,300.00"],
        ]
    )
    transactions = HdfcParser().parse(path)

    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("1200.00")


def test_repeated_header_rows_are_dropped(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            [_HEADER[0], _HEADER[1], _HEADER[2], _HEADER[3],
             _HEADER[4], _HEADER[5], _HEADER[6]],
            ["01/09/25", "SWIGGY 123456789012", "", "01/09/25",
             "", "450.00", "23,500.00"],
            [_HEADER[0], _HEADER[1], _HEADER[2], _HEADER[3],
             _HEADER[4], _HEADER[5], _HEADER[6]],
            ["02/09/25", "ZOMATO 987654321098", "", "02/09/25",
             "1,200.00", "", "22,300.00"],
        ]
    )
    transactions = HdfcParser().parse(path)

    assert len(transactions) == 2
    assert [t.amount for t in transactions] == [
        Decimal("450.00"),
        Decimal("1200.00"),
    ]


def test_rows_without_date_or_amount_are_ignored(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            [_HEADER[0], _HEADER[1], _HEADER[2], _HEADER[3],
             _HEADER[4], _HEADER[5], _HEADER[6]],
            ["01/09/25", "SWIGGY 123456789012", "", "01/09/25",
             "1,200.00", "", "23,500.00"],
            ["", "Ignored row, no date", "", "", "", "", ""],
            ["02/09/25", "Ignored row, no amounts", "", "02/09/25",
             "", "", "22,300.00"],
        ]
    )
    transactions = HdfcParser().parse(path)

    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("1200.00")


def test_missing_required_column_raises(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            ["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.",
             "Closing Balance"],
            ["01/09/25", "SWIGGY 123456789012", "1,200.00", "",
             "23,500.00"],
        ]
    )
    with pytest.raises(ValueError, match="missing"):
        HdfcParser().parse(path)


def test_no_valid_transactions_raises(tmp_path):
    path = _write_workbook(
        tmp_path,
        [
            [_HEADER[0], _HEADER[1], _HEADER[2], _HEADER[3],
             _HEADER[4], _HEADER[5], _HEADER[6]],
            ["01/09/25", "", "", "01/09/25", "", "", ""],
        ]
    )
    with pytest.raises(ValueError, match="no valid transactions"):
        HdfcParser().parse(path)


def test_parse_date_formats():
    parser = HdfcParser()

    assert parser._parse_date("05/09/2025") == date(2025, 9, 5)
    assert parser._parse_date("05/09/25") == date(2025, 9, 5)
    assert parser._parse_date("05-09-2025") == date(2025, 9, 5)
    assert parser._parse_date("05.09.2025") == date(2025, 9, 5)
    assert parser._parse_date("not a date") is None


def test_parse_amount_variants():
    parser = HdfcParser()

    assert parser._parse_amount("1,200.00") == Decimal("1200.00")
    assert parser._parse_amount("₹ 1,200.00") == Decimal("1200.00")
    assert parser._parse_amount("") is None
    assert parser._parse_amount("N/A") is None