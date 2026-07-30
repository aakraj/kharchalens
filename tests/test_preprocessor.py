from kharchalens.merchant.preprocessing import NarrationPreprocessor


def test_remove_numbers():

    result = NarrationPreprocessor.preprocess(
        "UPI 123456 AMAZON 998877"
    )

    assert result == "AMAZON"

def test_keep_words():

    result = NarrationPreprocessor.preprocess(
        "AMAZON SELLER SERVICES"
    )

    assert result == "AMAZON SELLER SERVICES"

def test_remove_pos():

    result = NarrationPreprocessor.preprocess(
        "POS 512967XXXXXX8643 MAKEMYTRIP INDIA"
    )

    assert result == "MAKEMYTRIP INDIA"


def test_remove_upi():

    result = NarrationPreprocessor.preprocess(
        "UPI AMAZON"
    )

    assert result == "AMAZON"


def test_remove_neft():

    result = NarrationPreprocessor.preprocess(
        "NEFT DR PPF"
    )

    assert result == "PPF"