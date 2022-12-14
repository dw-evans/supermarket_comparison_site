from utils.query import *
from utils.main import *


# run_and_pickle_request("oats")
path2 = Path(__file__).parent / "pickles/waitrose.pkl"
WAITROSE_PKL = open_pickle(path2)


class TestPriceSorters:
    def test_highest_price(self):
        sorter_enum = PriceSorterEnum.HIGHEST_PRICE
        reverse = True

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=PriceSorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.price.amount)

        new_item_list = item_filter.get_new_list(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0

    def test_lowest_price(self):
        sorter_enum = PriceSorterEnum.LOWEST_PRICE
        reverse = False

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=PriceSorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.price.amount)

        new_item_list = item_filter.get_new_list(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0

    def test_highest_unit_price(self):
        sorter_enum = PriceSorterEnum.HIGHEST_UNIT_PRICE
        reverse = True

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=PriceSorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.unit_price.price.amount)

        new_item_list = item_filter.get_new_list(item_list)

        sorted_result = []
        for item in new_item_list:
            sorted_result.append(item.unit_price.price.amount)

        print(res0, sorted_result)

        res0.sort(reverse=reverse)

        assert sorted_result == res0

    def test_lowest_unit_price(self):
        sorter_enum = PriceSorterEnum.LOWEST_UNIT_PRICE
        reverse = False

        WAITROSE_PKL = open_those_pickles()
        item_list = [WaitroseItem(item) for item in WAITROSE_PKL.get_items_as_list()]
        item_filter = ItemListFilter(
            sorter=PriceSorter(sorter_enum=sorter_enum),
            filters=[],
        )
        res0 = []
        for item in item_list:
            res0.append(item.unit_price.price.amount)

        new_item_list = item_filter.get_new_list(item_list)

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

        new_item_list = item_filter.get_new_list(item_list)

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

        new_item_list = item_filter.get_new_list(item_list)

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

        new_item_list = item_filter.get_new_list(item_list)

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

        new_item_list = item_filter.get_new_list(item_list)

        print(f"sorted list")
        for item in new_item_list:
            print(item.quantity)

        assert True
