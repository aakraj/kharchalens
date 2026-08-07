from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from kharchalens.models import TransactionType
from kharchalens.parser import SbiParser


def _raw_statement() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Savings Account", "", "", "", "", "", ""],
            ["Value Date", "Post Date", "Details", "Ref No/Cheque No",
             "₹ Debit", "₹ Credit", "Balance"],
            ["04/01/2026", "05/01/2026", "UPI/CR - MR TEST PERSON",
             "SBIN0000000001", "", "2,000.00", "2,398.82"],
            ["05/01/2026", "06/01/2026", "ATM WDL - 9999",
             "000000000011", "1,000.00", "", "1,398.82"],
        ]
    )


def _parse(monkeypatch, raw: pd.DataFrame):
    parser = SbiParser()
    monkeypatch.setattr(
        SbiParser,
        "_read_statement",
        lambda self, path, password=None: raw,
    )
    return parser.parse("dummy.xls")


def test_header_alias_mapping():
    parser = SbiParser()
    assert parser._column_for_header("Value Date") == "value_date"
    assert parser._column_for_header("Post Date") == "post_date"
    assert parser._column_for_header("Details") == "details"
    assert parser._column_for_header("Ref No/Cheque No") == "ref"
    assert parser._column_for_header("₹ Debit") == "debit"
    assert parser._column_for_header("₹ Credit") == "credit"
    assert parser._column_for_header("Balance") == "balance"


def test_find_header_row_skips_account_header(monkeypatch):
    raw = _raw_statement()
    parser = SbiParser()
    header_row = parser._find_header_row(raw)
    assert header_row == 1


def test_parse_sbi_excel_credit(monkeypatch):
    transactions = _parse(monkeypatch, _raw_statement())

    assert len(transactions) == 2

    transaction = transactions[0]
    assert transaction.date == date(2026, 1, 5)
    assert transaction.transaction_type == TransactionType.CREDIT
    assert transaction.amount == Decimal("2000.00")
    assert transaction.balance == Decimal("2398.82")
    assert transaction.narration == "UPI/CR - MR TEST PERSON"
    assert transaction.reference_number == "SBIN0000000001"


def test_parse_sbi_excel_debit(monkeypatch):
    transactions = _parse(monkeypatch, _raw_statement())

    transaction = transactions[1]
    assert transaction.date == date(2026, 1, 6)
    assert transaction.transaction_type == TransactionType.DEBIT
    assert transaction.amount == Decimal("1000.00")
    assert transaction.balance == Decimal("1398.82")


def test_amount_suffix_boolean_stripped(monkeypatch):
    raw = pd.DataFrame(
        [
            ["Value Date", "Details", "₹ Debit", "₹ Credit", "Balance"],
            ["05/01/2026", "NEFT CR-MR X", "", "1,250.00", "1,500.00 Dr"],
        ]
    )
    transactions = _parse(monkeypatch, raw)

    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("1250.00")
    assert transactions[0].transaction_type == TransactionType.CREDIT
    assert transactions[0].balance == Decimal("1500.00")


def test_no_valid_transactions(monkeypatch):
    empty = pd.DataFrame(
        [
            ["Value Date", "Details", "₹ Debit", "₹ Credit", "Balance"],
            ["05/01/2026", "", "", "", ""],
        ]
    )
    with pytest.raises(ValueError):
        _parse(monkeypatch, empty)