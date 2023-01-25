from utils.query import *
from utils.main import *


# test the item list filter thing
import random


def test_1():
    c = Currency.GBP
    u = Unit.KG

    test_filter = ItemListFilter(
        sorter=Sorter(SorterEnum.HIGHEST_PRICE),
        filters=[
            Filter.PriceFilter(Price(0, c), Price(50, c)),
            Filter.PriceFilter(UnitPrice(0, c, u), UnitPrice(0, c, u)),
        ],
    )
    print(random.randint(0, 100))
    item_list = [
        Item(
            description=str(i),
            price=Price(float(random.randint(0, 100)), c),
            quantity=Quantity(random.randint(0, 5), u),
        )
        for i in range(10)
    ]

    print("initial")
    for item in item_list:
        print(item.description, item.price, item.quantity, item.unit_price)

    search_result = SearchResult(item_list)
    filtered_and_sorted_list = search_result.filter_and_sort(test_filter)

    print("sorted")
    for item in filtered_and_sorted_list:
        print(item.description, item.price, item.quantity, item.unit_price)

    assert True


def test2():

    c = Currency.GBP
    u = [Unit.KG, Unit.ML, Unit.NULL]

    item_list = [
        Item(
            description=str(i),
            price=Price(float(random.randint(0, 100)), c),
            quantity=Quantity(random.randint(0, 5), u[random.randint(0, 2)]),
        )
        for i in range(10)
    ]

    print("initial")
    for item in item_list:
        print(item.description, item.price, item.quantity)

    my_filter = Filter.UnitTypeFilter(UnitType.VOLUME)

    filtered_list = my_filter.get_filtered_list(item_list)

    print("filtered")
    for item in filtered_list:
        print(item.description, item.price, item.quantity)

    assert True


# run_and_pickle_request("oats")
path2 = Path(__file__).parent / "pickles/waitrose.pkl"
WAITROSE_PKL = open_pickle(path2)


class TestPriceSorters:
    def test_highest_price(self):
        sorter_enum = SorterEnum.HIGHEST_PRICE
        reverse = True

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=Sorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.price.amount)

        new_item_list = item_filter.filter_and_sort(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0

    def test_lowest_price(self):
        sorter_enum = SorterEnum.LOWEST_PRICE
        reverse = False

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=Sorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.price.amount)

        new_item_list = item_filter.filter_and_sort(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0

    def test_highest_unit_price(self):
        sorter_enum = SorterEnum.HIGHEST_UNIT_PRICE
        reverse = True

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=Sorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.unit_price.price.amount)

        new_item_list = item_filter.filter_and_sort(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.unit_price.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0

    def test_lowest_unit_price(self):
        sorter_enum = SorterEnum.LOWEST_UNIT_PRICE
        reverse = False

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=Sorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.unit_price.price.amount)

        new_item_list = item_filter.filter_and_sort(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.unit_price.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0


class TestQuantitySorters:
    """Should really create a demo set including all edge cases for this... maybe later"""

    def test_highest_quantity(self):
        # this seems to be working. Should be reviewed later
        sorter_type = QuantitySorterEnum.HIGHEST
        reverse = True

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=QuantitySorter(sorter_enum=sorter_type),
            filters=[],
        )

        res0 = []
        print("original list:")
        for item in item_list:
            print(item.quantity, item.quantity.to_si())
            # res0.append(item.quantity.to_si().amount)

        new_item_list = item_filter.filter_and_sort(item_list)

        sorted_result = []
        print("sorted list:")
        for item in new_item_list:
            print(item.quantity, item.quantity.to_si())
            sorted_result.append(item.quantity.to_si().amount)

        # print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert True

    def test_lowest_quantity(self):
        # this seems to be working. Should be reviewed later
        sorter_type = QuantitySorterEnum.LOWEST
        reverse = True

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=QuantitySorter(sorter_enum=sorter_type),
            filters=[],
        )

        res0 = []
        print("original list:")
        for item in item_list:
            print(item.quantity, item.quantity.to_si())
            # res0.append(item.quantity.to_si().amount)

        new_item_list = item_filter.filter_and_sort(item_list)

        sorted_result = []
        print("sorted list:")
        for item in new_item_list:
            print(item.quantity, item.quantity.to_si())
            sorted_result.append(item.quantity.to_si().amount)

        # print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert True


class TestPriceFilters:
    def test_price_filter(self):

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=None,
            filters=[
                PriceFilter(
                    price_low=Price(0, Currency.GBP),
                    price_high=Price(2, Currency.GBP),
                )
            ],
        )
        for item in item_list:
            print(item.price)

        new_item_list = item_filter.filter_and_sort(item_list)

        print(f"sorted list")
        for item in new_item_list:
            print(item.price)

        assert True


class TestQuantityFilter:
    def test_quantity_filter(self):
        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=None,
            filters=[
                QuantityFilter(
                    qty_low=Quantity(0, Unit.KG), qty_high=Quantity(0.5, Unit.KG)
                )
            ],
        )
        for item in item_list:
            print(item.quantity)

        new_item_list = item_filter.filter_and_sort(item_list)

        print(f"sorted list")
        for item in new_item_list:
            print(item.quantity)

        assert True
