from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from kharchalens.models import TransactionType
from kharchalens.parser import (
    HdfcPdfParser,
    PdfIncorrectPassword,
    PdfPasswordRequired,
)


def _word(x0: float, text: str) -> tuple[float, float, float, str]:
    return (x0, x0 + 10.0, 10.0, text)


def _header_line() -> list[tuple[float, float, float, str]]:
    return [
        _word(40, "Date"),
        _word(80, "Narration"),
        _word(200, "Chq./Ref.No."),
        _word(290, "Value"),
        _word(320, "Dt"),
        _word(345, "Withdrawal"),
        _word(380, "Amt."),
        _word(405, "Deposit"),
        _word(430, "Amt."),
        _word(465, "Closing"),
        _word(500, "Balance"),
    ]


def _parse(
        monkeypatch,
        lines: list[list[tuple[float, float, float, str]]],
):
    parser = HdfcPdfParser()
    monkeypatch.setattr(
        HdfcPdfParser,
        "_extract_word_rows",
        lambda self, path, password=None: lines,
    )
    return parser.parse("dummy.pdf")


def test_single_deposit_transaction(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(40, "04/01/16"),
                _word(100, "NEFT CR-SBIN0014517-MR BINAY KUMAR SHAW"),
                _word(210, "SBIN516004007390"),
                _word(295, "04/01/16"),
                _word(410, "2,000.00"),
                _word(470, "2,398.82"),
            ],
        ],
    )

    assert len(transactions) == 1

    transaction = transactions[0]
    assert transaction.date == date(2016, 1, 4)
    assert transaction.transaction_type == TransactionType.CREDIT
    assert transaction.amount == Decimal("2000.00")
    assert transaction.balance == Decimal("2398.82")
    assert transaction.reference_number == "SBIN516004007390"
    assert (
        transaction.narration
        == "NEFT CR-SBIN0014517-MR BINAY KUMAR SHAW"
    )


def test_withdrawal_and_deposit_disambiguated(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(40, "05/01/16"),
                _word(100, "POS SHOP"),
                _word(210, "00000012345678A1"),
                _word(295, "05/01/16"),
                _word(355, "100.00"),
                _word(470, "398.82"),
            ],
            [
                _word(40, "06/01/16"),
                _word(100, "NEFT CR-OTHER"),
                _word(210, "N011160121345626"),
                _word(295, "06/01/16"),
                _word(410, "2,600.00"),
                _word(470, "2,998.82"),
            ],
        ],
    )

    assert [t.transaction_type for t in transactions] == [
        TransactionType.DEBIT,
        TransactionType.CREDIT,
    ]
    assert transactions[0].amount == Decimal("100.00")
    assert transactions[1].amount == Decimal("2600.00")


def test_multiline_narration(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(40, "04/01/16"),
                _word(100, "NEFT CR-SBIN0014517-MR BINAY KUMAR SHAW"),
            ],
            [
                _word(100, "-BINAY KUMAR SHAW-SBIN516004007390"),
                _word(210, "SBIN516004007390"),
                _word(295, "04/01/16"),
                _word(410, "2,000.00"),
                _word(470, "2,398.82"),
            ],
        ],
    )

    assert len(transactions) == 1
    assert transactions[0].narration == (
        "NEFT CR-SBIN0014517-MR BINAY KUMAR SHAW "
        "-BINAY KUMAR SHAW-SBIN516004007390"
    )


def test_comma_formatted_amounts(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(40, "11/01/16"),
                _word(100, "SALARY-123 STORES E COMMERCE PRIVATE LIMITED"),
                _word(210, "0000000000096388"),
                _word(295, "11/01/16"),
                _word(410, "18,396.00"),
                _word(470, "19,783.37"),
            ],
        ],
    )

    assert transactions[0].amount == Decimal("18396.00")
    assert transactions[0].balance == Decimal("19783.37")


def test_furniture_and_page_breaks_skipped(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            [_word(60, "HDFC"), _word(90, "BANK"), _word(200, "We understand your world")],
            [_word(30, "Page No:"), _word(70, "1")],
            _header_line(),
            [
                _word(40, "04/01/16"),
                _word(100, "SALARY-123 STORES E COMMERCE PRIVATE LIM"),
                _word(210, "00000079522696A1"),
                _word(295, "04/01/16"),
                _word(410, "18,396.00"),
                _word(470, "19,783.37"),
            ],
            [_word(60, "HDFC"), _word(90, "BANK"), _word(140, "LIMITED")],
            [_word(30, "Closing"), _word(80, "balance"), _word(120, "includes"), _word(170, "funds")],
            [_word(30, "Download"), _word(90, "to"), _word(120, "read"), _word(160, "ad-free")],
        ],
    )

    assert len(transactions) == 1
    assert (
        transactions[0].narration
        == "SALARY-123 STORES E COMMERCE PRIVATE LIM"
    )
    assert transactions[0].balance == Decimal("19783.37")


def test_summary_totals_row_not_absorbed(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(40, "31/01/16"),
                _word(100, "LAST DEBIT"),
                _word(210, "00000012345678A1"),
                _word(295, "31/01/16"),
                _word(355, "500.00"),
                _word(470, "7,398.82"),
            ],
            # Grand-total row: text (or figures) present in BOTH the
            # withdrawal and deposit columns. Must not be appended.
            [
                _word(80, "TOTAL"),
                _word(210, "TOTALS"),
                _word(355, "1,234.00"),
                _word(410, "9,876.00"),
                _word(470, "16,382.00"),
            ],
        ],
    )

    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("500.00")
    assert transactions[0].balance == Decimal("7398.82")


def test_next_page_account_info_not_absorbed(monkeypatch):
    def pointy(top: float, x0: float, text: str) -> tuple[float, float, float, str]:
        return (x0, x0 + 10.0, top, text)

    parser = HdfcPdfParser()
    lines = [
        _header_line(),
        [
            pointy(700.0, 40, "31/01/16"),
            pointy(700.0, 100, "LAST DEBIT OF PAGE ONE"),
            pointy(700.0, 210, "00000012345678A1"),
            pointy(700.0, 295, "31/01/16"),
            pointy(700.0, 355, "500.00"),
            pointy(700.0, 470, "7,398.82"),
        ],
        # Next page: a fresh account-info block with words whose left edges
        # fall inside the withdrawal/deposit column ranges. These must not
        # be appended to the previous page's last transaction.
        [
            pointy(40.0, 402, "XXXX"),
            pointy(40.0, 405, "XXXX"),
            pointy(40.0, 420, "3421"),
            pointy(40.0, 470, "9,876.54"),
        ],
        _header_line(),
        [
            pointy(120.0, 40, "01/02/16"),
            pointy(120.0, 100, "CREDIT AFTER PAGE BREAK"),
            pointy(120.0, 210, "00000098765432B2"),
            pointy(120.0, 295, "01/02/16"),
            pointy(120.0, 410, "1,000.00"),
            pointy(120.0, 470, "8,398.82"),
        ],
    ]
    monkeypatch.setattr(
        HdfcPdfParser,
        "_extract_word_rows",
        lambda self, path, password=None: lines,
    )

    transactions = parser.parse("dummy.pdf")

    assert len(transactions) == 2
    assert transactions[0].amount == Decimal("500.00")
    assert transactions[0].balance == Decimal("7398.82")
    assert "XXXX" not in transactions[0].narration
    assert transactions[1].amount == Decimal("1000.00")


def test_missing_header_raises(monkeypatch):
    with pytest.raises(ValueError, match="table"):
        _parse(
            monkeypatch,
            [
                [_word(40, "04/01/16"), _word(100, "SOME SHOP")],
            ],
        )


def test_empty_extraction_raises(monkeypatch):
    with pytest.raises(ValueError, match="scanned"):
        _parse(monkeypatch, [])


def test_hdfc_pdf_parser_end_to_end():
    path = Path(__file__).parent / "fixtures" / "hdfc_sample.pdf"
    transactions = HdfcPdfParser().parse(path)

    assert len(transactions) == 7
    assert transactions[0].narration == "POS 532676XXXXXX3201"
    assert transactions[2].narration == (
        "SALARY-123 STORES E COMMERCE -PRIVATE LIMITED"
    )
    assert transactions[6].amount == Decimal("2078.00")
    assert transactions[6].balance == Decimal("0.11")
    assert [t.transaction_type for t in transactions] == [
        TransactionType.DEBIT,
        TransactionType.CREDIT,
        TransactionType.CREDIT,
        TransactionType.DEBIT,
        TransactionType.CREDIT,
        TransactionType.CREDIT,
        TransactionType.CREDIT,
    ]


def _encrypted_fixture() -> Path:
    return Path(__file__).parent / "fixtures" / "hdfc_sample_encrypted.pdf"


def test_password_protected_pdf_requires_password():
    with pytest.raises(PdfPasswordRequired):
        HdfcPdfParser().parse(_encrypted_fixture())


def test_password_protected_pdf_wrong_password():
    with pytest.raises(PdfIncorrectPassword):
        HdfcPdfParser().parse(_encrypted_fixture(), password="wrongpass")


def test_password_protected_pdf_correct_password():
    transactions = HdfcPdfParser().parse(
        _encrypted_fixture(), password="secret123"
    )
    assert len(transactions) == 7
    assert transactions[2].narration == (
        "SALARY-123 STORES E COMMERCE -PRIVATE LIMITED"
    )


def test_password_ignored_on_plain_pdf():
    path = Path(__file__).parent / "fixtures" / "hdfc_sample.pdf"
    transactions = HdfcPdfParser().parse(path, password="whatever")
    assert len(transactions) == 7
