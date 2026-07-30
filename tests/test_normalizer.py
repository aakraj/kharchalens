from kharchalens.merchant import NarrationNormalizer


def test_uppercase():
    assert (
            NarrationNormalizer.normalize("upi-zomato")
            == "UPI ZOMATO"
    )


def test_multiple_separators():
    assert (
            NarrationNormalizer.normalize(
                "UPI/ZOMATO_ONLINE-ORDER"
            )
            == "UPI ZOMATO ONLINE ORDER"
    )


def test_multiple_spaces():
    assert (
            NarrationNormalizer.normalize(
                "UPI    ZOMATO     ORDER"
            )
            == "UPI ZOMATO ORDER"
    )