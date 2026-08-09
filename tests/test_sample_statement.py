from pathlib import Path

import pytest

from kharchalens.dashboard.summary import build_summary
from kharchalens.enrichment import TransactionEnricher
from kharchalens.parser import HdfcParser, IciciParser

SAMPLE_DIR = (
    Path(__file__).resolve().parent.parent
    / "kharchalens"
    / "sample_data"
)

ICICI_SAMPLE = SAMPLE_DIR / "sample_statement_icici.xlsx"
HDFC_SAMPLE = SAMPLE_DIR / "sample_statement_hdfc.xlsx"

SAMPLE_ROWS = 230
SAMPLE_MONTHS = 12


@pytest.mark.parametrize(
    "path, parser",
    [
        (ICICI_SAMPLE, IciciParser),
        (HDFC_SAMPLE, HdfcParser),
    ],
)
def test_sample_statement_exists(path, parser):
    assert path.exists()
    assert path.stat().st_size > 0


@pytest.mark.parametrize(
    "path, parser",
    [
        (ICICI_SAMPLE, IciciParser),
        (HDFC_SAMPLE, HdfcParser),
    ],
)
def test_sample_statement_parses(path, parser):
    transactions = parser().parse(str(path))

    assert len(transactions) == SAMPLE_ROWS


@pytest.mark.parametrize(
    "path, parser",
    [
        (ICICI_SAMPLE, IciciParser),
        (HDFC_SAMPLE, HdfcParser),
    ],
)
def test_sample_statement_has_twelve_months(path, parser):
    transactions = parser().parse(str(path))

    months = {t.date.strftime("%Y-%m") for t in transactions}

    assert len(months) == SAMPLE_MONTHS


@pytest.mark.parametrize(
    "path, parser",
    [
        (ICICI_SAMPLE, IciciParser),
        (HDFC_SAMPLE, HdfcParser),
    ],
)
def test_sample_statement_merchants_recognized(path, parser):
    enricher = TransactionEnricher()
    transactions = [
        enricher.enrich_transaction(t)
        for t in parser().parse(str(path))
    ]

    merchants = {t.merchant for t in transactions}

    assert {"Swiggy", "Zomato", "Amazon", "Electricity Bill"} <= merchants
    assert "Income tax" not in merchants


@pytest.mark.parametrize(
    "path, parser",
    [
        (ICICI_SAMPLE, IciciParser),
        (HDFC_SAMPLE, HdfcParser),
    ],
)
def test_sample_statement_average_monthly_spend(path, parser):
    transactions = parser().parse(str(path))
    summary = build_summary(transactions)

    assert summary["month_count"] == SAMPLE_MONTHS
    assert summary["average_monthly_spend"] > 0