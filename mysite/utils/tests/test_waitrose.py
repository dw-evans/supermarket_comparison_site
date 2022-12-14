from __future__ import annotations

from utils.main import *
from utils.query import *

# from utils.main import qa


def test_waitroseitem_qty_from_regex1():
    a = "6x35g"
    res = WaitroseItem.get_quantity_from_string(a)

    assert res == Quantity(6 * 35, Unit.G)


def test_waitroseitem_qty_from_regex2():
    a = "6litre"
    res = WaitroseItem.get_quantity_from_string(a)

    assert res == Quantity(6, Unit.L)


def test_waitroseitem_price_from_str():
    a = 6.00
    res = WaitroseItem.get_price_from_float(a)

    assert res == Price(6.00, Currency.GBP)
