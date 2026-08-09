from pathlib import Path

from kharchalens.dashboard.summary import build_summary
from kharchalens.enrichment import TransactionEnricher
from kharchalens.parser import IciciParser

SAMPLE_PATH = (
    Path(__file__).resolve().parent.parent
    / "kharchalens"
    / "sample_data"
    / "sample_statement.xlsx"
)


def test_sample_statement_exists():
    assert SAMPLE_PATH.exists()
    assert SAMPLE_PATH.stat().st_size > 0


def test_sample_statement_parses_as_icici():
    transactions = IciciParser().parse(str(SAMPLE_PATH))

    assert len(transactions) == 32


def test_sample_statement_has_multiple_months():
    transactions = IciciParser().parse(str(SAMPLE_PATH))

    months = {t.date.strftime("%Y-%m") for t in transactions}

    assert len(months) == 3


def test_sample_statement_merchants_recognized():
    enricher = TransactionEnricher()
    transactions = [
        enricher.enrich_transaction(t)
        for t in IciciParser().parse(str(SAMPLE_PATH))
    ]

    merchants = {t.merchant for t in transactions}

    assert {"Swiggy", "Zomato", "Amazon", "Electricity Bill"} <= merchants
    assert "Income tax" not in merchants


def test_sample_statement_average_monthly_spend():
    transactions = IciciParser().parse(str(SAMPLE_PATH))
    summary = build_summary(transactions)

    assert summary["month_count"] == 3
    assert summary["average_monthly_spend"] > 0
