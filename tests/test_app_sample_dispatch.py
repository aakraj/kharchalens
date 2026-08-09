from pathlib import Path

import pytest

import app

SAMPLE_DIR = (
    Path(__file__).resolve().parent.parent
    / "kharchalens"
    / "sample_data"
)


def _parse_sample(filename, password=None):
    data = (SAMPLE_DIR / filename).read_bytes()
    return app._parse_statement(data, ".xlsx", password, "")


@pytest.mark.parametrize(
    "filename, expected_bank",
    [
        ("sample_statement_hdfc.xlsx", "HDFC"),
        ("sample_statement_icici.xlsx", "ICICI"),
    ],
)
def test_sample_dispatch_selects_correct_bank(filename, expected_bank):
    """HDFC must beat SBI in bank detection, or HDFC samples show as SBI."""
    _, bank = _parse_sample(filename)

    assert bank == expected_bank