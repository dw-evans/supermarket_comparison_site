from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import re
import pickle
from pathlib import Path


from .query import WaitroseRequest, AsdaRequest
from .query import to_pickle


from abc import ABC, abstractmethod


class Currency(Enum):
    # store standardized currency information
    # in future, be able to compare pricing of a shop internationally.
    GBP = "gbp"
    NZD = "nzd"

    @staticmethod
    def exchange_rate(currency1: Currency, currency2: Currency) -> float:
        # calculate the exchange rate between two currencies
        e = {
            Currency.GBP: 1,
            Currency.NZD: 1.90,
        }
        return e[currency2] / e[currency1]

    def get_exchange_rate(self, currency2: Currency) -> float:
        # get the exchange rate from self to another currency
        return self.__class__.exchange_rate(self, currency2)

    def __str__(self):
        return self.value.upper()


class UnitType(Enum):
    # standardize unit types for consistency
    WEIGHT = "weight"
    VOLUME = "volume"
    OTHER = "other"


class Unit(Enum):
    # Enum of units of measurement
    EA = ("ea", UnitType.OTHER)
    NULL = ("N/A", UnitType.OTHER)
    PCS = ("pcs", UnitType.OTHER)

    KG = ("kg", UnitType.WEIGHT)
    KG_TYP = ("kg (typ)", UnitType.WEIGHT)
    G = ("g", UnitType.WEIGHT)

    L = ("l", UnitType.VOLUME)
    ML = ("ml", UnitType.VOLUME)
    CL = ("cl", UnitType.VOLUME)

    @property
    def unit_type(self):
        return self.value[1]

    def get_type(self):
        return self.unit_type

    def get_repr(self):
        return self.value[0]

    def __str__(self):
        return self.value[0].upper()

    @staticmethod
    def units_are_compatible(unit1: Unit, unit2: Unit):
        # check the compatibility of units for conversion
        type1 = unit1.unit_type
        type2 = unit2.unit_type

        if not type1 == type2:
            print(f"Units incompliant of types: {type1}, {type2}")
            return False
        if type1 == UnitType.OTHER:
            print(f"Unit Type is of {type1}, skipping")
            return False
        return True

    @classmethod
    def conversion_factor(cls, unit1: Unit, unit2: Unit) -> float:
        # determine the conversion factor for a unit conversion

        # if units arent compatible, return
        if not cls.units_are_compatible(unit1, unit2):
            return

        type1 = unit1.unit_type

        # weight units
        if type1 == UnitType.WEIGHT:
            e = {
                Unit.KG: 1,
                Unit.KG_TYP: 1,
                Unit.G: 1000,
            }
            return e[unit2] / e[unit1]
        # volume units
        if type1 == UnitType.VOLUME:
            e = {
                Unit.L: 1,
                Unit.ML: 1000,
                Unit.CL: 100,
            }
            return e[unit2] / e[unit1]
        return

    # something like convert_to_si_units


class Store(Enum):
    WAITROSE = "waitrose"
    ASDA = "asda"
    NULL = "null"


@dataclass
class Price:
    """stores price in amount and currency"""

    amount: float
    curr: Currency

    # def __post_init__(self):
    #     if self.currency is None:
    #         self.currency = Currency.GBP

    def get_amount(self):
        return self.amount

    def get_currency(self):
        return self.curr

    def convert_to(self, to_currency: Currency) -> Price:
        return Price(
            amount=self.amount * Currency.exchange_rate(self.curr, to_currency),
            curr=to_currency,
        )

    def __str__(self):
        return f"{self.amount:.2f} {self.curr.__str__()}"

    def __add__(self, rhs: Price):
        c = self.curr
        if rhs.curr != c:
            rhs = rhs.convert_to(c)
        return Price(self.amount + rhs.amount, c)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __sub__(self, rhs: Price):
        c = self.curr
        if rhs.curr != c:
            rhs = rhs.convert_to(c)
        return Price(self.amount - rhs.amount, c)

    __rsub__ = __sub__

    def __mul__(self, rhs: float | Price):
        if type(rhs) == Price:
            c = self.curr
            if rhs.curr != c:
                rhs = rhs.convert_to(c)
                return Price(self.amount * rhs.amount, c)
        else:
            return Price(self.amount * rhs, self.curr)

    __rmul__ = __mul__

    def __truediv__(self, rhs: float):
        c = self.curr
        if rhs.curr != c:
            rhs = rhs.convert_to(c)
        return Price(self.amount / rhs.amount, c)

    def __floordiv__(self, rhs: float):
        c = self.curr
        if rhs.curr != c:
            rhs = rhs.convert_to(c)
        return Price(self.amount // rhs.amount, c)


@dataclass
class Quantity:
    """stores a quantity amount and a unit"""

    amount: float
    unit: Unit

    def __post_init__(self):
        self.debug = ""

    def get_amount(self):
        return self.amount

    def get_unit(self):
        return self.unit

    def convert_to(self, to_unit: Unit) -> Quantity:
        if Unit.units_are_compatible(self.unit, to_unit):
            cf = Unit.conversion_factor(self.unit, to_unit)
            return Quantity(
                amount=self.amount * cf,
                unit=to_unit,
            )
        return self

    def __str__(self) -> str:
        if self.unit == Unit.NULL:
            return f"{self.amount} {self.unit} ({self.debug})"
        return f"{self.amount} {self.unit}"

    def to_si(self) -> Quantity:
        """Returns quantity in SI_units if applicable, else returns self"""
        # Convert weights to SI
        if self.unit.unit_type == UnitType.WEIGHT:
            return self.convert_to(Unit.KG)
        # Convert volumes to SI
        elif self.unit.unit_type == UnitType.VOLUME:
            return self.convert_to(Unit.L)
        # return self for non convertible units
        return self


@dataclass
class UnitPrice(Price):
    per_unit: Unit

    def get_price(self):
        return self

    def get_per_unit(self):
        return self.per_unit

    def __str__(self):
        return f"{super().__str__()} per {self.per_unit.__str__()}"

    @classmethod
    def calculate(cls, price: Price, quantity=Quantity):

        # if the amount is zero just return the price
        # if quantity.amount == 0:
        #     return price

        # calculate the quantity in the si quantity (kg/L/ea etc.)
        si_quantity = quantity.to_si()

        return cls(
            amount=price.amount / si_quantity.amount,
            curr=price.curr,
            per_unit=si_quantity.unit,
        )

    def convert_to(self, to_currency: Currency) -> UnitPrice:
        converted_price = super().convert_to(to_currency)
        return UnitPrice(
            amount=converted_price.amount,
            curr=converted_price.curr,
            per_unit=self.per_unit,
        )


import uuid


@dataclass
class Item(ABC):
    # generic item class for uniform access to variables.
    store: Store = Store.NULL
    description: str = "No description"
    price: Price = Price(0, Currency.GBP)
    quantity: Quantity = Quantity(0, Unit.NULL)
    thumbnail: str = field(repr=False, default="No thumbnail")
    is_null: bool = False

    def __post_init__(self):
        # todo replace this with just string concatentation to remove time-dependency as it causes duplication
        self.identifier = uuid.uuid4()

    def get_price(self):
        return self.price

    def get_quantity(self):
        return self.quantity

    @property
    def unit_price(self):
        return UnitPrice.calculate(
            price=self.price,
            quantity=self.quantity,
        )


class StoreUnitMap(Enum):
    class Waitrose(Enum):
        pass


# map from response json string to local unit system
# would probably be best to use embedded enum classes - see above
STORE_UNIT_MAP = {
    Store.WAITROSE: {
        "litre": Unit.L,
        "ml": Unit.ML,
        "kg": Unit.KG,
        "g": Unit.G,
        "s": Unit.PCS,
        "cl": Unit.CL,
    },
    Store.ASDA: {
        "l": Unit.L,
        "kg": Unit.KG,
        "g": Unit.G,
        "pk": Unit.PCS,
    },
}

"""
TODO
need to implement something for:
"Typical weight 0.3kg"
"drained 160g"

"""


class WaitroseItem(Item):
    # converting the waitrose json output into correct item structure
    def __init__(self, raw_item):
        self.raw_item = raw_item
        self.is_null = False

        self.store = Store.WAITROSE
        self.description = self.fetch_description()
        self.price = self.fetch_price()
        self.quantity = self.fetch_quanity()
        self.thumbnail = self.fetch_thumbnail()

        super().__post_init__()

    @staticmethod
    def get_quantity_from_string(string: str) -> Quantity:
        # regex to find a few different cases for waitrose

        print(f"Extracting quantity info from string='{string}'")

        qty_info = re.findall(r"\D+|\d*\.?\d+", string.strip(" "))
        # print(qty_info)
        # handle the 12x300g cases
        if qty_info[1].lower() == "x":
            amount = float(qty_info[0]) * float(qty_info[2])
        else:
            amount = float(qty_info[0])
        try:
            unit = Unit(STORE_UNIT_MAP[Store.WAITROSE][qty_info[-1]])
        except:
            unit = Unit.NULL

        quantity = Quantity(
            amount=amount,
            unit=unit,
        )
        quantity.debug = string

        return quantity

    @staticmethod
    def get_price_from_float(flt: float) -> Price:
        currency = Currency.GBP
        return Price(flt, currency)

    def fetch_description(self) -> str:
        try:
            return self.raw_item["searchProduct"]["name"]
        except:
            self.is_null = True
            return ""

    def fetch_price(self) -> Price:
        try:
            amount = self.raw_item["searchProduct"]["currentSaleUnitPrice"]["price"][
                "amount"
            ]
            currency = Currency.GBP
            return Price(amount, currency)
        except:
            return Price(0, Currency.GBP)

    def get_quantity_root(self) -> "dict or str":
        # pulls the raw root of quantity strying
        return self.raw_item["searchProduct"]["size"]

    def fetch_quanity(self) -> Quantity:
        try:
            size = self.get_quantity_root()
            return self.get_quantity_from_string(size)

        except:
            q = Quantity(1, Unit.NULL)
            try:
                a = self.raw_item["searchProduct"]["typicalWeight"]
                q.debug = a.__str__()
                try:
                    amount = a["amount"]
                    if a["uom"] == "KGM":
                        unit = Unit.KG_TYP
                    q.amount = amount
                    q.unit = unit
                except:
                    pass
            except:
                try:
                    q.debug = self.raw_item["searchProduct"][
                        "defaultQuantity"
                    ].__str__()
                except:
                    pass
            return q

    def fetch_thumbnail(self):
        try:
            return self.raw_item["searchProduct"]["thumbnail"]
        except:
            return ""


class AsdaItem(Item):
    # Converting the asda json output into item dataclass structure
    def __init__(self, raw_item):
        self.raw_item = raw_item

        self.store = Store.ASDA
        self.description = self.fetch_description()
        self.thumbnail = self.fetch_thumbnail()
        self.price = self.fetch_price()
        self.quantity = self.fetch_quanity()
        self.is_null = False

    # todo add try excepts to each of these
    def fetch_description(self) -> str:
        return self.raw_item["item"]["name"]

    def fetch_price(self) -> Price:
        return Price(
            float(self.raw_item["price"]["price_info"]["price"][1:]), Currency.GBP
        )

    def fetch_quanity(self) -> Quantity:
        size = self.raw_item["item"]["extended_item_info"]["weight"]
        qty_info = re.findall(r"\D+|\d*\.?\d+", size.strip(" "))
        if qty_info[1].lower == "x":
            amount = float(qty_info[0]) * float(qty_info[2])
        else:
            amount = float(qty_info[0])

        try:
            unit = Unit(STORE_UNIT_MAP[Store.ASDA.value][qty_info[-1]])
        except:
            unit = Unit.NULL

        return Quantity(
            amount=amount,
            unit=unit,
        )

    def fetch_thumbnail(self) -> str:
        return "https://ui.assets-asda.com/dm/asdagroceries/{}?$ProdList$=&fmt=webp&qlt=50".format(
            self.raw_item["item"]["upc_numbers"][0]
        )


# Filtering things


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
            print("sorting by highest price")
            return self.sorter(item_list, self._item_price_amount, reverse=True)
        elif sorter_enum == SorterEnum.LOWEST_PRICE:
            print("sortin by lowest price")
            return self.sorter(item_list, self._item_price_amount, reverse=False)
        #  Unit price sorting

        elif sorter_enum == SorterEnum.HIGHEST_UNIT_PRICE:
            print("sorting by highest unit price")
            return self.sorter(item_list, self._item_unit_price_amount, reverse=True)
        elif sorter_enum == SorterEnum.LOWEST_UNIT_PRICE:
            print("sorting by lowest unit price")
            return self.sorter(item_list, self._item_unit_price_amount, reverse=False)
        # Quantity sorting
        elif sorter_enum == SorterEnum.HIGHEST_QUANTITY:
            print("sorting by unit_type then highest quantity")
            new_item_list = self.sorter(item_list, self._item_unit_type, reverse=False)
            new_item_list = self.sorter(
                new_item_list, self._item_quantity_amount_in_si, reverse=True
            )
            return new_item_list
        elif sorter_enum == SorterEnum.LOWEST_QUANTITY:
            print("sorting by unit_type then lowest quantity")
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


from functools import partial


class Filter:
    class AttributeFilter(ABC):
        """generic attribute filter"""

        def get_filtered_list(self, item_list: list[Item]):
            return item_list
            pass

    @dataclass
    class PriceFilter(AttributeFilter):
        # maybe we can do a filter by unit price one too... would need to be paired with a sorter first probably.
        price_low: Price
        price_high: Price

        def __post_init__(self):
            if self.price_low is None:
                self.price_low = Price(0.0)
            if self.price_high is None:
                self.price_high = Price(500.0)
            self.base_currency = self.price_low.curr
            self.price_high = self.price_high.convert_to(self.base_currency)

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
    class QuantityFilter(AttributeFilter):
        # maybe we can do a filter by unit price one too... would need to be paired with a sorter first probably.
        qty_low: Quantity
        qty_high: Quantity

        def __post_init__(self):
            if self.qty_low is None:
                self.qty_low = Quantity(0, Unit.KG)
            if self.qty_high is None:
                self.qty_high = Quantity(20, Unit.KG)
            self.base_unit = self.qty_low.unit
            self.qty_high = self.qty_high.convert_to(self.base_unit)

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

    @dataclass
    class UnitTypeFilter(AttributeFilter):
        unit_type_accept_list: list[UnitType] = field(default_factory=list)

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
            if len(self.unit_type_accept_list) == 0:
                return item_list
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
            if filter_type in self.unit_type_accept_list:
                self.unit_type_accept_list.remove(filter_type)
            else:
                self.unit_type_accept_list.append(filter_type)


# import random

# c = Currency.GBP
# u = [Unit.KG, Unit.ML, Unit.NULL]

# item_list = [
#     Item(
#         description=str(i),
#         price=Price(float(random.randint(0, 100)), c),
#         quantity=Quantity(random.randint(0, 5), u[random.randint(0, 2)]),
#     )
#     for i in range(10)
# ]

# print("initial")
# for item in item_list:
#     print(item.description, item.price, item.quantity)


# my_filter = Filter.UnitTypeFilter(UnitType.VOLUME)


# filtered_list = my_filter.get_filtered_list(item_list)

# print("filtered")
# for item in filtered_list:
#     print(item.description, item.price, item.quantity)


@dataclass
class SearchResult:
    initial_list: list[Item] = field(default_factory=list)

    def __post_init__(self):
        # map the sorted lists to the intiial on pre-processing
        self.sorted_list = self.initial_list
        self.sorted_and_filtered_list = self.initial_list

    def filter_and_sort(self, item_list_filter: ItemListFilter):
        # returns a filter and sorted list, stores them in the object too.
        self.sorted_list = item_list_filter._sort(self.sorted_list)
        self.sorted_and_filtered_list = item_list_filter._filter(self.sorted_list)
        return self.sorted_and_filtered_list


# ItemListFilter.filter_and_sort(SearchResult.sorted_list)


class ItemListFilter:
    def __init__(
        self,
        sorter: Sorter = None,
        filters: list[Filter.AttributeFilter] = [],
    ):
        self.sorter = sorter
        self.filters = filters

    def _sort(self, item_list: list[Item]) -> list[Item]:

        result = item_list.copy()

        if self.sorter:
            result = self.sorter.get_sorted_list(item_list)

        return result

    def _filter(self, item_list: list[Item]) -> list[Item]:

        result = item_list.copy()

        for filter_i in self.filters:
            result = filter_i.get_filtered_list(result)

        return result

    def clear_filters(self):
        self.filters = []

    def set_filters(self, filters: list[Filter.AttributeFilter]):
        self.filters = filters

    def get_state(self):
        # something to quickly get the states of all the filters,
        # e.g. qty/price/unit-price upper/lower... description, unit type
        return
        return {"sorter": self.sorter, "filters": self.filters}


if __name__ == "__main__":
    print("done")
