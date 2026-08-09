from kharchalens.merchant import MerchantResolver
from kharchalens.models import TransactionType


def test_zomato():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "UPI-ZOMATO ONLINE ORDER-12345"
            )
            == "Zomato"
    )


def test_swiggy():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "UPI-SWIGGY LIMITED-999"
            )
            == "Swiggy"
    )


def test_amazon():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "AMAZON SELLER SERVICES"
            )
            == "Amazon"
    )


def test_unknown():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "SOME RANDOM SHOP"
            )
            == "Unknown"
    )


def test_credit_merchant_ignored_for_debit():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "MMT/IMPS/621420810316/Ravi Gowri/SBIN0015997 NACH trxn",
                TransactionType.DEBIT,
            )
            == "Unknown"
    )


def test_credit_merchant_fires_for_credit():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "CEMTEX DEP   ACHCr NACH000 00000056295 MAZAGON DOCK S",
                TransactionType.CREDIT,
            )
            == "Dividend Credit"
    )


def test_credit_merchant_fires_when_type_unknown():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "CEMTEX DEP   ACHCr NACH 512 00000056295 MAZAGON DOCK S",
            )
            == "Dividend Credit"
    )


def test_short_keyword_not_matched_across_words():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "MMT/IMPS/DEBIT/RENT/June 2026",
            )
            == "Unknown"
    )


def test_keyword_matched_as_contiguous_words():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "UPI/AIR INDIA/E8QRW3 0000012345",
            )
            == "Air India"
    )


def test_keyword_matched_when_glued_into_one_word():
    resolver = MerchantResolver()

    assert (
            resolver.resolve(
                "UPI/ACTFIBERNET/0000012345",
            )
            == "ACT Fibernet"
    )