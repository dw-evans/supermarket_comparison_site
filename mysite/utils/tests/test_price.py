from utils.main import Price, Currency


def test_price_convert_to():

    a = Price(100, Currency.GBP)
    b = a.convert_to(Currency.NZD)
    c = b.convert_to(Currency.GBP)

    assert c == Price(100, Currency.GBP)
