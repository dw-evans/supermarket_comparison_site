from utils.main import *


# Currency  testing
from utils.main import Currency


def test_price_convert_to():

    a = Price(100, Currency.GBP)
    b = a.convert_to(Currency.NZD)
    c = b.convert_to(Currency.GBP)

    assert c == Price(100, Currency.GBP)


# Unit Price testing
from utils.main import Price, Quantity, UnitPrice


def test_unit_price_weight():
    # test that unit price calculation is working
    a = Price(2, Currency.GBP)
    b = Quantity(2000, Unit.G)

    res1 = UnitPrice.calculate(price=a, quantity=b)

    assert res1 == UnitPrice(Price(1, Currency.GBP), per_unit=Unit.KG)


def test_unit_price_volume():
    # test that unit price calculation is working
    c = Price(10, Currency.GBP)
    d = Quantity(250, Unit.ML)

    res2 = UnitPrice.calculate(price=c, quantity=d)
    default = UnitPrice(Price(40, Currency.GBP), per_unit=Unit.L)

    print(res2)
    print(default)

    assert res2 == default
