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
            Currency.NZD: 1.91,
        }
        return e[currency2] / e[currency1]

    def get_exchange_rate(self, currency2: Currency) -> float:
        # get the exchange rate from self to another currency
        return self.__class__.exchange_rate(self, currency2)

    def __str__(self):
        return self.value.upper()


class UnitTypes(Enum):
    # standardize unit types for consistency
    WEIGHT = "weight"
    VOLUME = "volume"
    OTHER = "other"


class Unit(Enum):
    # Enum of units of measurement
    EA = ("ea", UnitTypes.OTHER)
    NULL = ("N/A", UnitTypes.OTHER)
    PCS = ("pcs", UnitTypes.OTHER)

    KG = ("kg", UnitTypes.WEIGHT)
    G = ("g", UnitTypes.WEIGHT)

    L = ("l", UnitTypes.VOLUME)
    ML = ("ml", UnitTypes.VOLUME)

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
        if type1 == UnitTypes.OTHER:
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
        if type1 == UnitTypes.WEIGHT:
            e = {
                Unit.KG: 1,
                Unit.G: 1000,
            }
            return e[unit2] / e[unit1]
        # volume units
        if type1 == UnitTypes.VOLUME:
            e = {
                Unit.L: 1,
                Unit.ML: 1000,
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
    currency: Currency

    # def __post_init__(self):
    #     if self.currency is None:
    #         self.currency = Currency.GBP

    def get_amount(self):
        return self.amount

    def get_currency(self):
        return self.currency

    def convert_to(self, to_currency: Currency) -> Price:
        return Price(
            amount=self.amount * Currency.exchange_rate(self.currency, to_currency),
            currency=to_currency,
        )

    def __str__(self):
        return f"{self.amount:.2f} {self.currency.__str__()}"


@dataclass
class Quantity:
    """stores a quantity amount and a unit"""

    amount: float
    unit: Unit

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
        return f"{self.amount} {self.unit}"

    def to_si(self) -> Quantity:
        """Returns quantity in SI_units if applicable, else returns self"""
        # Convert weights to SI
        if self.unit.unit_type == UnitTypes.WEIGHT:
            return self.convert_to(Unit.KG)
        # Convert volumes to SI
        elif self.unit.unit_type == UnitTypes.VOLUME:
            return self.convert_to(Unit.L)
        # return self for non convertible units
        return self


@dataclass
class UnitPrice:
    price: Price
    per_unit: Unit

    def get_price(self):
        return self.price

    def get_per_unit(self):
        return self.per_unit

    def __str__(self):
        return f"{self.price}/{self.per_unit}"

    @classmethod
    def calculate(cls, price: Price, quantity=Quantity):

        if quantity.amount == 0:
            return price

        si_quantity = quantity.to_si()

        return cls(
            price=Price(
                amount=price.amount / si_quantity.amount,
                currency=price.currency,
            ),
            per_unit=si_quantity.unit,
        )


@dataclass
class Item(ABC):
    # generic item class for uniform access to variables.
    store: Store
    description: str
    price: Price
    quantity: Quantity
    thumbnail: str = field(repr=False)
    is_null: bool

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


# map from response json string to local unit system
STORE_UNIT_MAP = {
    Store.WAITROSE: {
        "litre": Unit.L,
        "ml": Unit.ML,
        "kg": Unit.KG,
        "g": Unit.G,
        "s": Unit.PCS,
    },
    Store.ASDA: {
        "l": Unit.L,
        "kg": Unit.KG,
        "g": Unit.G,
        "pk": Unit.PCS,
    },
}


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

    @staticmethod
    def get_quantity_from_string(string: str) -> Quantity:
        # regex to find a few different cases for waitrose
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

        return Quantity(
            amount=amount,
            unit=unit,
        )

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
            return Quantity(0, Unit.NULL)

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
    LOWEST_QUANTITY = "lowest-quantity"


# class QuantitySorterEnum(Enum):
#     """stores quantity sorting types"""

#     HIGHEST = 'highest_quantity'
#     LOWEST = 'lowest-quantity'


class AttributeSorter(ABC):
    """genetic attribute sorter"""

    def __init__(self, sorter_type: Enum) -> None:
        super().__init__()
        self.sorter_type = sorter_type

    def get_sorted_list(self) -> list[Item]:
        pass

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


class PriceSorter(AttributeSorter):
    """price sorter class"""

    def __init__(self, sorter_enum: SorterEnum) -> None:
        self.sorter_type = sorter_enum

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
        return item.unit_price.price.amount

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
            return super().sorter(item_list, self._item_price_amount, reverse=True)
        elif sorter_enum == SorterEnum.LOWEST_PRICE:
            print("sortin by lowest price")
            return super().sorter(item_list, self._item_price_amount, reverse=False)
        #  Unit price sorting

        elif sorter_enum == SorterEnum.HIGHEST_UNIT_PRICE:
            print("sorting by highest unit price")
            return super().sorter(item_list, self._item_unit_price_amount, reverse=True)
        elif sorter_enum == SorterEnum.LOWEST_UNIT_PRICE:
            print("sorting by lowest unit price")
            return super().sorter(
                item_list, self._item_unit_price_amount, reverse=False
            )
        # Quantity sorting
        elif sorter_enum == SorterEnum.HIGHEST_QUANTITY:
            print("sorting by unit_type then highest quantity")
            new_item_list = super().sorter(
                new_item_list, self._item_unit_type, reverse=False
            )
            new_item_list = super().sorter(
                new_item_list, self._item_quantity_amount_in_si, reverse=True
            )
            return new_item_list
        elif sorter_enum == SorterEnum.LOWEST_QUANTITY:
            print("sorting by unit_type then lowest quantity")
            new_item_list = super().sorter(
                new_item_list, self._item_unit_type, reverse=False
            )
            new_item_list = super().sorter(
                new_item_list, self._item_quantity_amount_in_si, reverse=False
            )
            return new_item_list

        else:
            print(
                f"no compatible type of type:{sorter_enum} found, returning original list"
            )
            return item_list


# class QuantitySorter(AttributeSorter):
#     def __init__(self, sorter_enum: SorterEnum) -> None:
#         self.sorter_type = sorter_enum

#     def get_sorted_list(self, item_list: list[Item]) -> list[Item]:
#         """returns a sorted list, first by a default sort by unit type then by quantity amount in si units of course"""
#         new_item_list = item_list.copy()
#         sorter_enum = self.sorter_type
#         if sorter_enum == SorterEnum.HIGHEST_QUANTITY:
#             print("sorting by unit_type then highest quantity")
#             new_item_list = super().sorter(
#                 new_item_list, self._item_unit_type, reverse=False
#             )
#             new_item_list = super().sorter(
#                 new_item_list, self._item_quantity_amount_in_si, reverse=True
#             )
#             return new_item_list
#         elif sorter_enum == SorterEnum.LOWEST_QUANTITY:
#             print("sorting by unit_type then lowest quantity")
#             new_item_list = super().sorter(
#                 new_item_list, self._item_unit_type, reverse=False
#             )
#             new_item_list = super().sorter(
#                 new_item_list, self._item_quantity_amount_in_si, reverse=False
#             )
#             return new_item_list

#         pass


class AttributeFilter(ABC):
    """generic attribute filter"""

    def get_filtered_list(self):
        pass

    def filter_func(
        item_list: list[Item], item_filter_func: function(Item), reverse: bool
    ) -> list[Item]:
        """generic item list filter with input function not used yet"""
        new_item_list = [item for item in item_list if item_filter_func(item)]
        return new_item_list


from functools import partial


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
        self.base_currency = self.price_low.currency
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
    def _quantity_amount_in_si_is_between(item: Item, low: Quantity, high: Quantity):
        return low.to_si().amount <= item.quantity.to_si().amount <= high.to_si().amount

    @staticmethod
    def _quantity_is_of_same_unit_type(item: Item, unit_type: UnitTypes):
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


class ItemListFilter:
    def __init__(
        self,
        initial_list=list[Item],
        sorter: AttributeSorter = None,
        filters: list[AttributeFilter] = [],
    ):
        self.initial_list = initial_list
        self.sorter = sorter
        self.filters = filters
        # self.sorted_list = initial_list.copy()

    def get_new_list(self, item_list: list[Item]) -> list[Item]:
        # return self.sorter.get_sorted_list(item_list)

        new_item_list = item_list.copy()

        if self.sorter:
            new_item_list = self.sorter.get_sorted_list(item_list)

        self.sorted_list = new_item_list.copy()

        if self.filters:
            for filter_i in self.filters:
                new_item_list = filter_i.get_filtered_list(new_item_list)

        return new_item_list

    def run(self) -> list[Item]:
        # consider changing run to operate on the sorted list, not the initial list
        self.filtered_list = self.get_new_list(self.initial_list)
        return self.filtered_list


if __name__ == "__main__":
    print("done")
