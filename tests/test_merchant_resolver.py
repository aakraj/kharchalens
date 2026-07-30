from kharchalens.merchant import MerchantResolver


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