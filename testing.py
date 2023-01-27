from enum import Enum


class Store(Enum):
    WAITROSE = "waitrose"
    ASDA = "asda"


class StoreUnitMap(Enum):
    def __new__(cls, *args):
        value = args[0]
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, value, unit_dict):
        self.unit_dict = unit_dict

    WAITROSE = Store.WAITROSE, {"dict": 1}
    ASDA = Store.ASDA, {"dict": 2}


print(StoreUnitMap.WAITROSE.unit_dict)
print(StoreUnitMap.ASDA)

print("a")
