from __future__ import annotations

from dataclasses import dataclass, field
from abc import ABC
from functools import partial
from enum import Enum

from .datatypes import Item, Price, UnitPrice, Currency, Quantity, Unit, UnitType

from .searchrequest import GrocerySearchRequest


class SearchEnum(Enum):
    def __new__(
        cls, value, search_request_class: GrocerySearchRequest, item_class: Item
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(
        self, value, search_request_class: GrocerySearchRequest, item_class: Item
    ):
        self.search_request_class = search_request_class
        self.item_class = item_class


class SorterEnum(Enum):
    """stores price sorting types"""

    HIGHEST_PRICE = "highest_price"
    LOWEST_PRICE = "lowest_price"
    HIGHEST_UNIT_PRICE = "highest_unit_price"
    LOWEST_UNIT_PRICE = "lowest_unit_price"
    HIGHEST_QUANTITY = "highest_quantity"
    LOWEST_QUANTITY = "lowest_quantity"


class Sorter:
    """generic sorter class"""

    def __init__(self, sorter_enum: SorterEnum) -> None:
        self.sorter_type = sorter_enum

    @staticmethod
    def sorter(
        item_list: list[Item], item_sort_attribute_func: function, reverse: bool
    ) -> list[Item]:
        """generic item list sorter with input function, Default sort from low to high"""
        new_item_list = item_list.copy()
        new_item_list.sort(
            key=lambda item: item_sort_attribute_func(item), reverse=reverse
        )
        return new_item_list

    # these two functions are a bit shit
    @staticmethod
    def _item_price_amount(item: Item):
        # returns the item price amount
        return item.price.amount

    @staticmethod
    def _item_unit_price_amount(item: Item):
        # returns the item unit price
        if item.quantity.amount == 0:
            return item.price.amount
        return item.unit_price.amount

    @staticmethod
    def _item_quantity_amount_in_si(item: Item):
        return item.quantity.to_si().amount

    @staticmethod
    def _item_unit_type(item: Item):
        return item.quantity.unit.unit_type.value

    def get_sorted_list(self, item_list: list[Item]) -> list[Item]:
        """sorter function, returns a sorted list of items per the requested filter(sorter) type"""
        sorter_enum = self.sorter_type

        # Price sorting
        if sorter_enum == SorterEnum.HIGHEST_PRICE:
            # print("sorting by highest price")
            return self.sorter(item_list, self._item_price_amount, reverse=True)
        elif sorter_enum == SorterEnum.LOWEST_PRICE:
            # print("sortin by lowest price")
            return self.sorter(item_list, self._item_price_amount, reverse=False)
        #  Unit price sorting

        elif sorter_enum == SorterEnum.HIGHEST_UNIT_PRICE:
            # print("sorting by highest unit price")
            return self.sorter(item_list, self._item_unit_price_amount, reverse=True)
        elif sorter_enum == SorterEnum.LOWEST_UNIT_PRICE:
            # print("sorting by lowest unit price")
            return self.sorter(item_list, self._item_unit_price_amount, reverse=False)
        # Quantity sorting
        elif sorter_enum == SorterEnum.HIGHEST_QUANTITY:
            # print("sorting by unit_type then highest quantity")
            new_item_list = self.sorter(item_list, self._item_unit_type, reverse=False)
            new_item_list = self.sorter(
                new_item_list, self._item_quantity_amount_in_si, reverse=True
            )
            return new_item_list
        elif sorter_enum == SorterEnum.LOWEST_QUANTITY:
            # print("sorting by unit_type then lowest quantity")
            new_item_list = self.sorter(item_list, self._item_unit_type, reverse=False)
            new_item_list = self.sorter(
                new_item_list, self._item_quantity_amount_in_si, reverse=False
            )
            return new_item_list

        else:
            print(
                f"no compatible type of type:{sorter_enum} found, returning original list"
            )
            return item_list


class Filter:
    class AttributeFilter(ABC):
        """generic attribute filter"""

        def __post_init__(self):
            self.disable()

        def disable(self):
            self.is_enabled = False

        def enable(self):
            self.is_enabled = True

        def toggle_enable(self):
            self.is_enabled = not self.is_enabled

        def get_filtered_list(self, item_list: list[Item]):
            return item_list

    @dataclass
    class PriceFilter(AttributeFilter):
        # maybe we can do a filter by unit price one too... would need to be paired with a sorter first probably.
        price_low: Price | UnitPrice
        price_high: Price | UnitPrice

        def __post_init__(self):
            # if self.price_low is None:
            #     self.price_low = Price(0.0)
            # if self.price_high is None:
            #     self.price_high = Price(500.0)
            self.base_currency = self.price_low.curr
            self.price_high = self.price_high.convert_to(self.base_currency)
            super().__post_init__()

        @staticmethod
        def _price_amount_is_between(item: Item, lower: Price, upper: Price) -> bool:
            return (
                lower.convert_to(Currency.GBP).amount
                < item.price.convert_to(Currency.GBP).amount
                < upper.convert_to(Currency.GBP).amount
            )

        def get_filtered_list(self, item_list: list[Item]):
            return list(
                filter(
                    partial(
                        self._price_amount_is_between,
                        lower=self.price_low,
                        upper=self.price_high,
                    ),
                    item_list,
                )
            )

    @dataclass
    class UnitPriceFilter(PriceFilter):
        # just assume that the units are matching

        def __post_init__(self):
            try:
                if self.price_low.per_unit != self.price_high.per_unit:
                    print("Warning, not matching units")
            except:
                print(
                    f"Warning, prices not UnitPrices, price_low.type={type(self.price_low)}, price_low.type={type(self.price_low)}"
                )
            return super().__post_init__()

    @dataclass
    class QuantityFilter(AttributeFilter):
        # be aware that this inherently is a unittypefilter
        qty_low: Quantity
        qty_high: Quantity

        @dataclass
        class Weight:
            qty_low: Quantity
            qty_high: Quantity
            pass

        @dataclass
        class Volume:
            qty_low: Quantity
            qty_high: Quantity
            pass

        @dataclass
        class Other:
            qty_low: Quantity
            qty_high: Quantity
            pass

        def __post_init__(self):
            # if self.qty_low is None:
            #     self.qty_low = Quantity(0, Unit.KG)
            # if self.qty_high is None:
            #     self.qty_high = Quantity(20, Unit.KG)
            self.base_unit = self.qty_low.unit
            self.qty_high = self.qty_high.convert_to(self.base_unit)
            super().__post_init__()

        @staticmethod
        def _quantity_amount_in_si_is_between(
            item: Item, low: Quantity, high: Quantity
        ):
            return (
                low.to_si().amount
                <= item.quantity.to_si().amount
                <= high.to_si().amount
            )

        @staticmethod
        def _quantity_is_of_same_unit_type(item: Item, unit_type: UnitType):
            return item.quantity.unit.unit_type == unit_type

        def get_filtered_list(self, item_list: list[Item]):
            new_item_list = item_list.copy()
            # first filter out non compliant units
            new_item_list = list(
                filter(
                    partial(
                        self._quantity_is_of_same_unit_type,
                        unit_type=self.base_unit.unit_type,
                    ),
                    new_item_list,
                )
            )
            new_item_list = list(
                filter(
                    partial(
                        self._quantity_amount_in_si_is_between,
                        low=self.qty_low,
                        high=self.qty_high,
                    ),
                    new_item_list,
                )
            )
            return new_item_list

    @dataclass
    class DescriptionFilter(AttributeFilter):
        description: str

        def __post_init__(self):
            return super().__post_init__()

        @staticmethod
        def _item_description_contains_str(item: Item, sub_string: str):
            return sub_string in item.description

        def get_filtered_list(self, item_list: list[Item]):
            return list(
                filter(
                    partial(
                        self._item_description_contains_str, sub_string=self.description
                    ),
                    item_list,
                )
            )

    class UnitTypeFilter(AttributeFilter):
        # somehow something else breaks if the default factory is removed....

        # unit_type_accept_list: list[UnitType] = field(
        #     default_factory=[UnitType.VOLUME, UnitType.WEIGHT, UnitType.OTHER]
        # )

        def __init__(
            self,
            unit_type_accept_list=[
                UnitType.VOLUME,
                UnitType.WEIGHT,
                UnitType.OTHER,
            ],
        ):
            self.unit_type_accept_list = unit_type_accept_list
            self.__post_init__()

        # def __init__(self, unit_type_accept_list=[]):
        #     self.unit_type_accept_list: list[UnitType]

        def __post_init__(self):
            return super().__post_init__()

        @staticmethod
        def _item_unit_accept(item: Item, unit_type_accept_list: list[UnitType]):

            # print(f"item.quantity={item.quantity}")
            item_unit = item.quantity.unit
            for unit_type_accept in unit_type_accept_list:
                # print(
                #     f"id={item.identifier}, comparing: {item.quantity.unit.unit_type} to {unit_type_accept}"
                # )
                if item_unit.unit_type == unit_type_accept:
                    return True
            return False

        def get_filtered_list(self, item_list: list[Item]):
            # if len(self.unit_type_accept_list) == 0:
            #     return item_list
            return list(
                filter(
                    partial(
                        self._item_unit_accept,
                        unit_type_accept_list=self.unit_type_accept_list,
                    ),
                    item_list,
                )
            )

        def clear_filter_types(self):
            self.unit_type_accept_list = []
            return self

        def toggle_unit_type_accept_list(self, filter_type: UnitType):
            # print(f"toggling {filter_type}")
            if filter_type in self.unit_type_accept_list:
                # print(f"removing {filter_type}")
                self.unit_type_accept_list.remove(filter_type)
            else:
                # print(f"adding {filter_type}")
                self.unit_type_accept_list.append(filter_type)


@dataclass
class SearchResult:
    initial_list: list[Item] = field(default_factory=list)

    def __post_init__(self):
        # map the sorted lists to the intiial on pre-processing
        self.sorted_list = self.initial_list
        self._sorted_and_filtered_list = self.initial_list

    def filter_and_sort(self, item_list_filter: ItemListFilter):
        # returns a filter and sorted list, stores them in the object too.
        # put here so we can store the sorted lists as well as the original
        self.sorted_list = item_list_filter._sort(self.sorted_list)
        self._sorted_and_filtered_list = item_list_filter._filter(self.sorted_list)
        return self._sorted_and_filtered_list


class ItemListFilter:
    class AllFilters:
        def __init__(self):
            self.price_filter = Filter.PriceFilter(
                Price(0, Currency.GBP), Price(1000, Currency.GBP)
            )
            self.unit_price_filter = Filter.UnitPriceFilter(
                UnitPrice(0, Currency.GBP, Unit.KG),
                UnitPrice(10, Currency.GBP, Unit.KG),
            )
            self.quantity_filter = Filter.QuantityFilter(
                Quantity(0, Unit.KG), Quantity(10, Unit.KG)
            )
            self.unit_type_filter = Filter.UnitTypeFilter(
                [UnitType.VOLUME, UnitType.WEIGHT, UnitType.OTHER]
            )
            self.description_filter = Filter.DescriptionFilter("")

        def _filters_as_list(self) -> list[Filter.AttributeFilter]:
            s = self
            return [
                s.price_filter,
                s.unit_price_filter,
                s.quantity_filter,
                s.unit_type_filter,
                s.description_filter,
            ]

        def _filter(self, item_list: list[Item]):
            res = item_list.copy()
            for f in self._filters_as_list():
                if f.is_enabled:
                    res = f.get_filtered_list(res)
            return res

    def __init__(
        self,
    ):
        self.sorter: Sorter = None
        self.filters: ItemListFilter.AllFilters = ItemListFilter.AllFilters()

    def _sort(self, item_list: list[Item]) -> list[Item]:

        result = item_list.copy()

        if self.sorter:
            result = self.sorter.get_sorted_list(item_list)

        return result

    def _filter(self, item_list: list[Item]) -> list[Item]:

        res = item_list.copy()
        res = self.filters._filter(res)

        return res

    def clear_filters(self):
        self.filters = ItemListFilter.AllFilters()
