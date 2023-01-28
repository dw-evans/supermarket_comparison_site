from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import uuid
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
class UnitPrice(Price):
    per_unit: Unit

    def get_price(self):
        return self

    def get_per_unit(self):
        return self.per_unit

    def __str__(self):
        return f"{super().__str__()} per {self.per_unit.__str__()}"

    @classmethod
    def calculate(cls, price: Price, quantity: Quantity):

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
class Item(ABC):
    # generic item class for uniform access to variables.
    store = {"No Store": "No Store Specified"}
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
        try:
            return UnitPrice.calculate(
                price=self.price,
                quantity=self.quantity,
            )
        except:
            print(f"UnitPrice.calculate({self.price}, {self.quantity}) failed")
            return UnitPrice(self.price.amount, self.price.curr, self.quantity.unit)
