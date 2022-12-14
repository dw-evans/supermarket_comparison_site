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

    def get_type(self):
        return self.value[1]

    def get_repr(self):
        return self.value[0]

    def __str__(self):
        return self.value[0].upper()

    @staticmethod
    def units_are_compatible(unit1: Unit, unit2: Unit):
        # check the compatibility of units for conversion
        type1 = unit1.get_type()
        type2 = unit2.get_type()

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
        type1 = unit1.get_type()
        type2 = unit2.get_type()

        # if units arent compatible, return
        if not cls.units_are_compatible():
            return

        # weight units
        if type1 == UnitTypes.WEIGHT:
            e = {
                Unit.KG: 1,
                Unit.G: 0.001,
            }
            return e[type2] / e[type1]
        # volume units
        if type1 == UnitTypes.VOLUME:
            e = {
                Unit.L: 1,
                Unit.ML: 0.001,
            }
            return e[type2] / e[type1]
        return

    # something like convert_to_si_units


class Store(Enum):
    WAITROSE = "waitrose"
    ASDA = "asda"
    NULL = "null"


@dataclass
class Price:
    # stores price in amount and currency
    amount: float
    currency: Currency

    def convert_to(self, to_currency: Currency) -> Price:
        return Price(
            amount=self.amount * Currency.exchange_rate(self.currency, to_currency),
            currency=to_currency,
        )

    def __str__(self):
        return f"{self.amount:.2f} {self.currency.__str__()}"


@dataclass
class Quantity:
    # stores a quanity as a float and unit
    amount: float
    unit: Unit

    def convert_to(self, to_unit: Unit) -> Quantity:
        if Unit.units_are_compatible(self.unit, to_unit):
            return Quantity(
                amount=self.amount * Unit.conversion_factor(self.unit, to_unit),
                unit=to_unit,
            )
        return self

    def __str__(self):
        return f"{self.amount} {self.unit}"


@dataclass
class Item(ABC):
    # generic item class for uniform access to variables.
    store: Store
    description: str
    price: Price
    quantity: Quantity
    thumbnail: str = field(repr=False)
    is_null: bool

    @property
    def unit_price(self):
        return Price(self.price.amount / self.quantity.amount, self.price.currency)


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
        self.description = self.get_description()
        self.price = self.get_price()
        self.quantity = self.get_quanity()
        self.thumbnail = self.get_thumbnail()

    def get_description(self) -> str:
        try:
            return self.raw_item["searchProduct"]["name"]
        except:
            self.is_null = True
            return ""

    def get_price(self) -> Price:
        try:
            amount = self.raw_item["searchProduct"]["currentSaleUnitPrice"]["price"][
                "amount"
            ]
            currency = Currency.GBP
            return Price(amount, currency)
        except:
            return Price(0, Currency.GBP)

    def get_quantity_root(self):
        return self.raw_item["searchProduct"]["size"]

    def get_quanity(self) -> Quantity:
        try:
            size = self.get_quantity_root()
            qty_info = re.findall(r"\D+|\d*\.?\d+", size.strip(" "))
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
        except:
            return Quantity(0, Unit.NULL)

    def get_thumbnail(self):
        try:
            return self.raw_item["searchProduct"]["thumbnail"]
        except:
            return ""


class AsdaItem(Item):
    # Converting the asda json output into item dataclass structure
    def __init__(self, raw_item):
        self.raw_item = raw_item

        self.store = Store.ASDA
        self.description = self.get_description()
        self.thumbnail = self.get_thumbnail()
        self.price = self.get_price()
        self.quantity = self.get_quanity()
        self.is_null = False

    # todo add try excepts to each of these
    def get_description(self) -> str:

        return self.raw_item["item"]["name"]

    def get_price(self) -> Price:
        return Price(
            float(self.raw_item["price"]["price_info"]["price"][1:]), Currency.GBP
        )

    def get_quanity(self) -> Quantity:
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

    def get_thumbnail(self) -> str:
        return "https://ui.assets-asda.com/dm/asdagroceries/{}?$ProdList$=&fmt=webp&qlt=50".format(
            self.raw_item["item"]["upc_numbers"][0]
        )


# Filtering things
class ItemListFilters:
    class StoreFilterEnum(Enum):
        pass

    class PriceFilterEnum(Enum):
        HIGHEST = auto()
        LOWEST = auto()
        HIGHEST_BY_UNIT = auto()
        LOWEST_BY_UNIT = auto()
        pass

    class QuantityFilterEnum(Enum):
        HIGHEST = auto()
        LOWEST = auto()
        pass

    class PriceFilter:
        def filter(self, filter: ItemListFilters.PriceFilterEnum) -> list[Item]:
            if filter == ItemListFilters.PriceFilterEnum.HIGHEST:
                print("filtering by highest price")

    class StoreFilter:
        pass

    class QuantityFilter:
        pass


@dataclass
class ItemListFilterObj:
    store_filter: ItemListFilters.StoreFilter
    price_filter: ItemListFilters.PriceFilter
    quantity_filter: ItemListFilters.QuantityFilter


if __name__ == "__main__":
    print("done")
