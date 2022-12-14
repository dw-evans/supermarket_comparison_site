from utils.main import Quantity, Unit


def test_convert_to1():
    # test weight conversion
    a = Quantity(amount=1000, unit=Unit.G)

    assert a.convert_to(Unit.KG) == Quantity(1, Unit.KG)


def test_convert_to2():
    # test invalid conversion
    a = Quantity(amount=1000, unit=Unit.EA)

    assert a.convert_to(Unit.KG) == Quantity(1000, Unit.EA)


def test_convert_to3():
    # test volume conversion
    a = Quantity(amount=1000, unit=Unit.ML)

    assert a.convert_to(Unit.L) == Quantity(1, Unit.L)


def test_convert_to4():
    # test trivial conversion
    a = Quantity(amount=1000, unit=Unit.ML)

    assert a.convert_to(Unit.ML) == Quantity(1000, Unit.ML)
