from pathlib import Path

from kharchalens.parser import HdfcParser


def test_hdfc_parser():

    parser = HdfcParser()

    transactions = parser.parse(
        str(Path("sample_data") / "hdfc_sample.csv")
    )

    assert len(transactions) > 0