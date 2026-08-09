from datetime import date

from kharchalens.utils.date_utils import format_date


def test_format_date():
    assert format_date(date(2026, 9, 1)) == "01-Sep-2026"