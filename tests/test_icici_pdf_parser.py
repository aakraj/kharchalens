from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from kharchalens.models import TransactionType
from kharchalens.parser import IciciPdfParser, PdfIncorrectPassword, PdfPasswordRequired

_FIXTURES = Path(__file__).parent / "fixtures"


def _word(x0: float, x1: float, text: str) -> tuple[float, float, float, str]:
    return (x0, x1, 10.0, text)


def _banner() -> list[tuple[float, float, float, str]]:
    return [_word(0, 90, "ICICI Bank Ltd."), _word(100, 200, "Account Statement")]


def _debit_row() -> list[tuple[float, float, float, str]]:
    return [
        _word(28, 38, "1"),
        _word(40, 95, "02.08.2026"),
        _word(405, 440, "4,000.00"),
        _word(515, 548, "1,10,318.84"),
    ]


def _credit_row() -> list[tuple[float, float, float, str]]:
    return [
        _word(28, 38, "2"),
        _word(40, 95, "03.08.2026"),
        _word(450, 480, "2,000.00"),
        _word(515, 548, "1,12,318.84"),
    ]


def _narration(words: str) -> list[tuple[float, float, float, str]]:
    parts = words.split()
    items: list[tuple[float, float, float, str]] = []
    x = 120.0
    for part in parts:
        width = 10 + len(part)
        items.append(_word(x, x + width, part))
        x += width + 5
    return items


def _parse(monkeypatch, lines):
    parser = IciciPdfParser()
    monkeypatch.setattr(
        IciciPdfParser,
        "_extract_word_rows",
        lambda self, path, password=None: lines,
    )
    return parser.parse("dummy.pdf")


def test_icici_pdf_parses_transactions(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _banner(),
            _debit_row(),
            _narration("NEFT"),
            _credit_row(),
            _narration("UPI"),
        ],
    )

    assert len(transactions) == 2

    debit = transactions[0]
    assert debit.date == date(2026, 8, 2)
    assert debit.transaction_type == TransactionType.DEBIT
    assert debit.amount == Decimal("4000.00")
    assert debit.balance == Decimal("110318.84")

    credit = transactions[1]
    assert credit.date == date(2026, 8, 3)
    assert credit.transaction_type == TransactionType.CREDIT
    assert credit.amount == Decimal("2000.00")
    assert credit.balance == Decimal("112318.84")


def test_parse_dot_and_slash_dates(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _banner(),
            _debit_row()[:1] + [_word(40, 95, "03/08/2026")] + _debit_row()[2:],
            _narration("NEFT"),
            _credit_row()[:1] + [_word(40, 95, "03-08-2026")] + _credit_row()[2:],
            _narration("UPI"),
        ],
    )

    assert transactions[0].date == date(2026, 8, 3)
    assert transactions[1].date == date(2026, 8, 3)


def test_parse_multi_line_narration(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _banner(),
            _debit_row(),
            [_word(120, 200, "MYTRANSFER/PAYMENT"), _word(205, 260, "SOMEONE")],
            _credit_row(),
            _narration("UPI SOMEONE"),
        ],
    )

    assert len(transactions) == 2
    assert transactions[0].transaction_type == TransactionType.DEBIT


def test_rejects_non_icici_pdf(monkeypatch):
    with pytest.raises(ValueError, match="identify"):
        _parse(
            monkeypatch,
            [
                [_word(0, 60, "No ICICI here")],
                _debit_row(),
            ],
        )


def test_password_required():
    parser = IciciPdfParser()
    with pytest.raises(PdfPasswordRequired):
        parser.parse(str(_FIXTURES / "hdfc_sample_encrypted.pdf"))


def test_wrong_password():
    parser = IciciPdfParser()
    with pytest.raises(PdfIncorrectPassword) as excinfo:
        parser.parse(str(_FIXTURES / "hdfc_sample_encrypted.pdf"), password="nope")
    assert "password" in str(excinfo.value).lower()