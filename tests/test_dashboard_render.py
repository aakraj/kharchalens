from datetime import date
from decimal import Decimal

import pytest

from kharchalens.dashboard import (
    category_chart,
    charts,
    highlights,
    merchant_table,
)
from kharchalens.models import Transaction, TransactionKind, TransactionType


class FakeStreamlit:
    """Records Streamlit calls instead of rendering them."""

    def __init__(self):
        self.calls = []

    def subheader(self, *args, **kwargs):
        self.calls.append(("subheader", args, kwargs))

    def caption(self, *args, **kwargs):
        self.calls.append(("caption", args, kwargs))

    def markdown(self, *args, **kwargs):
        self.calls.append(("markdown", args, kwargs))

    def plotly_chart(self, *args, **kwargs):
        self.calls.append(("plotly_chart", args, kwargs))

    def dataframe(self, *args, **kwargs):
        self.calls.append(("dataframe", args, kwargs))

    def columns(self, *args, **kwargs):
        self.calls.append(("columns", args, kwargs))
        count = args[0] if len(args) == 1 and isinstance(args[0], int) else len(args)
        return [self] * count

    def header(self, *args, **kwargs):
        self.calls.append(("header", args, kwargs))


def _txn(
        day: int,
        amount: str,
        merchant: str | None = None,
        kind: TransactionKind = TransactionKind.PURCHASE,
        type_: TransactionType = TransactionType.DEBIT,
        month: int = 1,
) -> Transaction:
    return Transaction(
        date=date(2026, month, day),
        narration="NEFT DR TEST",
        amount=Decimal(amount),
        transaction_type=type_,
        merchant=merchant,
        kind=kind,
    )


def _sample() -> list[Transaction]:
    return [
        _txn(1, "1200.00", "Swiggy"),
        _txn(2, "800.00", "Swiggy", month=2),
        _txn(3, "2500.00", "Amazon", month=3),
        _txn(4, "100000.00", None, month=4),
        _txn(5, "150.00", "Netflix", month=5),
        _txn(5, "50000.00", "Salary", type_=TransactionType.CREDIT, month=5),
    ]


@pytest.fixture
def fake_st(monkeypatch):
    fake = FakeStreamlit()
    for module in (charts, category_chart, highlights, merchant_table):
        monkeypatch.setattr(module, "st", fake)
    return fake


def _figures(fake: FakeStreamlit) -> list:
    return [
        args[0]
        for call, args, _ in fake.calls
        if call == "plotly_chart"
    ]


def test_render_monthly_spending_builds_bar_chart(fake_st):
    charts.render_monthly_spending(_sample())

    figures = _figures(fake_st)
    assert len(figures) == 1
    fig = figures[0]
    assert len(fig.data) == 1
    assert list(fig.data[0].y) == [1200.0, 800.0, 2500.0, 100000.0, 150.0]


def test_render_monthly_spending_no_debits_does_nothing(fake_st):
    charts.render_monthly_spending(
        [_txn(1, "5000.00", "Salary", type_=TransactionType.CREDIT)]
    )

    assert _figures(fake_st) == []


def test_render_monthly_spending_shows_year_when_multiple(fake_st):
    txns = [
        Transaction(
            date=date(2025, 12, 5),
            narration="x",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.DEBIT,
            merchant="Swiggy",
        ),
        Transaction(
            date=date(2026, 1, 5),
            narration="x",
            amount=Decimal("200.00"),
            transaction_type=TransactionType.DEBIT,
            merchant="Swiggy",
        ),
    ]
    charts.render_monthly_spending(txns)

    fig = _figures(fake_st)[0]
    assert list(fig.layout.xaxis.ticktext) == ["Dec 25", "Jan 26"]


def test_render_top_merchants_builds_horizontal_bar(fake_st):
    charts.render_top_merchants(_sample())

    figures = _figures(fake_st)
    assert len(figures) == 1
    fig = figures[0]
    assert fig.data[0].orientation == "h"
    assert sorted(fig.data[0].y) == ["Amazon", "Netflix", "Swiggy", "🟡 Needs Review"]


def test_render_top_merchants_empty_noop(fake_st):
    charts.render_top_merchants([])

    assert _figures(fake_st) == []


def test_bar_colors_empty():
    assert charts.bar_colors([]) == []


def test_bar_colors_top_values_teal():
    colors = charts.bar_colors([10.0, 20.0, 100.0])

    assert colors[1] == charts.TEAL
    assert colors[2] == charts.TEAL
    assert len(set(colors)) == 2


def test_render_category_spending_builds_breakdown(fake_st):
    category_chart.render_category_spending(_sample())

    figures = _figures(fake_st)
    assert len(figures) == 1
    fig = figures[0]
    assert set(fig.data[0].y) == {"Lifestyle Spending"}


def test_render_category_spending_empty_noop(fake_st):
    category_chart.render_category_spending([])

    assert _figures(fake_st) == []


def test_render_highlights_paints_four_cards(fake_st):
    summary = {
        "total_credit": Decimal("50000.00"),
        "net_cash_flow": Decimal("46000.00"),
        "total_debit": Decimal("4000.00"),
        "transaction_count": 6,
        "month_count": 1,
        "average_monthly_spend": Decimal("4000.00"),
    }
    highlights.render_highlights(_sample(), summary)

    markdowns = [
        args[0]
        for call, args, _ in fake_st.calls
        if call == "markdown"
    ]
    assert len(markdowns) == 4
    assert "Highest Merchant" in markdowns[0]
    assert "Savings Rate" in markdowns[2]
    assert "Statement Period" in markdowns[3]
    assert "92.0%" in markdowns[2]


def test_render_highlights_no_transactions(fake_st):
    summary = {
        "total_credit": Decimal(0),
        "net_cash_flow": Decimal(0),
        "total_debit": Decimal(0),
        "transaction_count": 0,
        "month_count": 0,
        "average_monthly_spend": Decimal(0),
    }
    highlights.render_highlights([], summary)

    markdowns = [
        args[0]
        for call, args, _ in fake_st.calls
        if call == "markdown"
    ]
    assert "Highest Merchant" in markdowns[0]
    assert "-" in markdowns[0]
    assert "-" in markdowns[3]


def test_render_merchant_summary_builds_dataframe(fake_st):
    merchant_table.render_merchant_summary(_sample())

    dataframes = [
        args[0]
        for call, args, _ in fake_st.calls
        if call == "dataframe"
    ]
    assert len(dataframes) == 1
    assert dataframes[0].index.size == 4


def test_render_merchant_summary_empty_noop(fake_st):
    merchant_table.render_merchant_summary([])

    dataframes = [
        call
        for call, _, _ in fake_st.calls
        if call == "dataframe"
    ]
    assert dataframes == []