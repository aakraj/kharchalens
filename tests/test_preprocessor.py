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


def test_extract_keyword_upi():

    keyword = NarrationPreprocessor.extract_keyword(
        "UPI-ALL MARKET-ALLMARKET.96103871@HDFCBANK-HDFC0MERUPI-104083396687-UPI"
    )

    assert keyword == "ALL MARKET"


def test_extract_keyword_upi_with_spaces():

    keyword = NarrationPreprocessor.extract_keyword(
        "UPI - SWIGGY-PAYTM-9123456789@YBL"
    )

    assert keyword == "SWIGGY"


def test_extract_keyword_non_upi_keeps_full():

    keyword = NarrationPreprocessor.extract_keyword(
        "POS 512967XXXXXX8643 MAKE MY TRIP"
    )

    assert keyword == "MAKE MY TRIP"


def test_extract_keyword_pos_drops_masked_card():

    keyword = NarrationPreprocessor.extract_keyword(
        "POS 512967XXXXXX8643 GK ENTERPRISES V"
    )

    assert keyword == "GK ENTERPRISES V"


def test_extract_keyword_pos_no_card_keeps_rest():

    keyword = NarrationPreprocessor.extract_keyword(
        "POS R K ENTERPRISES"
    )

    assert keyword == "R K ENTERPRISES"


def test_extract_keyword_upi_empty_segment_falls_back():

    keyword = NarrationPreprocessor.extract_keyword(
        "UPI-"
    )

    assert keyword == "UPI-"