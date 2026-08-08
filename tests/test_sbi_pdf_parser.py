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


def _particulars_header() -> list[tuple[float, float, float, str]]:
    # SBI statements also ship with this classic layout.
    return [
        _word(30, 40, "Date"),
        _word(100, 150, "Particulars"),
        _word(300, 320, "Withdrawal"),
        _word(360, 380, "Deposit"),
        _word(420, 440, "Balance"),
    ]


def test_sbi_pdf_particulars_layout(monkeypatch):
    transactions = _parse(
        monkeypatch,
        [
            _particulars_header(),
            [
                _word(0, 25, "05/01/2026"),
                _word(100, 125, "NEFT"),
                _word(130, 145, "CR"),
                _word(370, 390, "2,000.00"),
                _word(430, 450, "2,398.82"),
            ],
        ],
    )

    assert len(transactions) == 1
    assert transactions[0].date == date(2026, 1, 5)
    assert transactions[0].transaction_type == TransactionType.CREDIT
    assert transactions[0].amount == Decimal("2000.00")
    assert transactions[0].balance == Decimal("2398.82")
    assert transactions[0].narration == "NEFT CR"


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


def test_sbi_pdf_no_header_geometry(monkeypatch):
    # A real SBI e-statement with NO column-header row: narration sits on the
    # line ABOVE each date/amount line, and amounts are right-aligned into
    # debit (~346), credit (~435) and balance (~512) bands.
    transactions = _parse(
        monkeypatch,
        [
            # narration lines (no date) precede their transaction's date line
            [
                _word(138, 150, "CEMTEX"),
                _word(174, 190, "DEP"),
                _word(197, 215, "ACHCr"),
            ],
            [
                _word(27, 40, "07/05/2025"),
                _word(82, 95, "07/05/2025"),
                _word(340, 470, "-"),
                _word(420, 520, "-"),
                _word(435, 442, "500.00"),
                _word(512, 530, "76,075.96"),
            ],
            [
                _word(138, 150, "UPI"),
                _word(160, 175, "DR"),
                _word(180, 190, "ZERODHA"),
            ],
            [
                _word(27, 40, "12/05/2025"),
                _word(82, 95, "12/05/2025"),
                _word(304, 320, "-"),
                _word(346, 352, "2,000.00"),
                _word(446, 460, "-"),
                _word(512, 513, "73,075.96"),
            ],
        ],
    )

    assert len(transactions) == 2

    first, second = transactions[0], transactions[1]
    assert first.date == date(2025, 5, 7)
    assert first.transaction_type == TransactionType.CREDIT
    assert first.amount == Decimal("500.00")
    assert first.balance == Decimal("76075.96")
    assert first.narration == "CEMTEX DEP ACHCr"

    assert second.date == date(2025, 5, 12)
    assert second.transaction_type == TransactionType.DEBIT
    assert second.amount == Decimal("2000.00")
    assert second.balance == Decimal("73075.96")
    assert second.narration == "UPI DR ZERODHA"