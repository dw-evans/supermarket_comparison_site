from __future__ import annotations

from enum import Enum


class Store(Enum):
    # WAITROSE = "waitrose"
    # ASDA = "asda"
    # NULL = "null"
    pass


class StoreUnitMap(Enum):

    # NULL = "null", {}

    def __new__(cls, store, dict):
        value = store  # copy the
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, unit_dict):
        self.unit_dict = unit_dict

    """
    unit_dict is of type:
    

    WAITROSE = (
        Store.WAITROSE,
        {
            <unit extracted from json>: Unit.<matching unit>
            "litre": Unit.L,
            "ml": Unit.ML,
            "kg": Unit.KG,
            "g": Unit.G,
            "s": Unit.PCS,
            "cl": Unit.CL,
        },
    )
    """
