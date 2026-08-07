from datetime import date
from decimal import Decimal

from kharchalens.models import TransactionType
from kharchalens.parser import SbiPdfParser


def _word(x0: float, x1: float, text: str) -> tuple[float, float, float, str]:
    return (x0, x1, 10.0, text)


def _header_line() -> list[tuple[float, float, float, str]]:
    # Column left-edges: value(0-40) post(40-130) details(130-200)
    # ref(200-250) debit(250-330) credit(330-380) balance(>=380).
    return [
        _word(30, 40, "Value"),
        _word(45, 55, "Date"),
        _word(95, 110, "Post"),
        _word(115, 125, "Date"),
        _word(130, 170, "Details"),
        _word(200, 210, "Ref"),
        _word(250, 290, "Debit"),
        _word(330, 360, "Credit"),
        _word(380, 410, "Balance"),
    ]


def _parse(monkeypatch, lines):
    parser = SbiPdfParser()
    monkeypatch.setattr(
        SbiPdfParser,
        "_extract_word_rows",
        lambda self, path, password=None: lines,
    )
    return parser.parse("dummy.pdf")


def test_sbi_pdf_credit_transaction(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(0, 25, "04/01/2026"),
                _word(40, 110, "05/01/2026"),
                _word(135, 145, "NEFT"),
                _word(150, 160, "CR"),
                _word(300, 340, "2,000.00"),
                _word(385, 400, "2,398.82"),
            ],
        ],
    )

    assert len(transactions) == 1

    transaction = transactions[0]
    assert transaction.date == date(2026, 1, 5)
    assert transaction.transaction_type == TransactionType.CREDIT
    assert transaction.amount == Decimal("2000.00")
    assert transaction.balance == Decimal("2398.82")
    assert transaction.narration == "NEFT CR"


def test_sbi_pdf_debit_transaction(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(0, 25, "05/01/2026"),
                _word(40, 110, "06/01/2026"),
                _word(135, 145, "ATM"),
                _word(160, 185, "WDL"),
                _word(210, 235, "SBIN0000000011"),
                _word(300, 310, "1,000.00"),
                _word(385, 400, "1,398.75"),
            ],
        ],
    )

    assert len(transactions) == 1

    transaction = transactions[0]
    assert transaction.date == date(2026, 1, 6)
    assert transaction.transaction_type == TransactionType.DEBIT
    assert transaction.amount == Decimal("1000.00")
    assert transaction.balance == Decimal("1398.75")
    assert transaction.reference_number == "SBIN0000000011"


def test_sbi_pdf_multi_line_narration(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _header_line(),
            [
                _word(0, 25, "05/01/2026"),
                _word(40, 110, "05/01/2026"),
                _word(135, 150, "UPI"),
                _word(160, 180, "CONTINUATION"),
                _word(300, 340, "500.00"),
                _word(385, 400, "600.00"),
            ],
        ],
    )

    assert len(transactions) == 1
    assert transactions[0].narration == "UPI CONTINUATION"


def test_sbi_pdf_invalid_layout(monkeypatch):
    parser = SbiPdfParser()
    monkeypatch.setattr(
        SbiPdfParser,
        "_extract_word_rows",
        lambda self, path, password=None: [[_word(10, 100, "garbage")]],
    )
    try:
        parser.parse("dummy.pdf")
        assert False, "expected a ValueError"
    except ValueError:
        pass