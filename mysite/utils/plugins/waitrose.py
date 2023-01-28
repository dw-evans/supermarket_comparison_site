from __future__ import annotations


import aenum
import re
import requests
from pathlib import Path

from ..datatypes import *
from ..store import Store, StoreUnitMap
from ..searchrequest import GrocerySearchRequest

# regster the store name in in the enum


def register():
    s = "waitrose"
    # if not s in set(item.value for item in Store):
    if not s in [store.value for store in Store]:
        aenum.extend_enum(Store, s.upper(), s.lower())

        s = Store.WAITROSE
        # if not s in set(item.value for item in Store):
        aenum.extend_enum(
            StoreUnitMap,
            s.value.upper(),
            (
                s,
                {
                    "litre": Unit.L,
                    "ml": Unit.ML,
                    "kg": Unit.KG,
                    "g": Unit.G,
                    "s": Unit.PCS,
                    "cl": Unit.CL,
                },
            ),
        )

        from ..search import SearchEnum

        s = Store.WAITROSE
        aenum.extend_enum(
            SearchEnum,
            s.value.upper(),
            (
                Store.WAITROSE,
                WaitroseRequest,
                WaitroseItem,
            ),
        )


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
    def _get_quantity_from_string(string: str) -> Quantity:
        # regex to find a few different cases for waitrose

        # print(f"Extracting quantity info from string='{string}'")

        qty_info = re.findall(r"\D+|\d*\.?\d+", string.strip(" "))
        # print(qty_info)
        # handle the 12x300g cases
        if qty_info[1].lower() == "x":
            amount = float(qty_info[0]) * float(qty_info[2])
        else:
            amount = float(qty_info[0])
        try:
            unit = Unit(StoreUnitMap(Store.WAITROSE).unit_dict[qty_info[-1]])
            # unit = Unit(STORE_UNIT_MAP[Store.WAITROSE][qty_info[-1]])
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

    def _get_quantity_root(self) -> "dict or str":
        # pulls the raw root of quantity strying
        return self.raw_item["searchProduct"]["size"]

    def fetch_quanity(self) -> Quantity:
        try:
            size = self._get_quantity_root()
            return self._get_quantity_from_string(size)

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


WAITROSE_MAX_REQUEST_SIZE = 128


class WaitroseRequest(GrocerySearchRequest):
    """Does a post request to the waitrose search api and stores the response
    Needs to be modified to handle item lists > 128 per page"""

    MAX_REQUEST_SIZE = 128

    def __init__(self, search_term: str, max_items: int = 5000):
        super().__init__()  # basically just for debugging at the moment

        self.search_term = search_term
        self.max_items = max_items

        self.multi_query()

        # self.query(search_term=search_term)

    def query(
        self, search_term: str, start: int, size: int = WAITROSE_MAX_REQUEST_SIZE
    ) -> "httpresponse":

        print(
            f"Sending request to waitrose.com for '{search_term}', start={start}, size={size}"
        )  # for debugging

        url = "https://www.waitrose.com/api/content-prod/v2/cms/publish/productcontent/search/-1"

        querystring = {"clientType": "WEB_APP"}

        payload = {
            "customerSearchRequest": {
                "queryParams": {
                    "size": size,
                    "searchTerm": search_term,
                    "sortBy": "RELEVANCE",
                    "searchTags": [],
                    "filterTags": [],
                    "orderId": "0",
                    "categoryLevel": 1,
                    "start": start,
                }
            }
        }
        headers = {"authorization": "Bearer unauthenticated"}

        return requests.request(
            "POST", url, json=payload, headers=headers, params=querystring
        )

    def get_total_items(self) -> int:
        return int(
            self.query(search_term=self.search_term, start=1, size=1).json()[
                "totalMatches"
            ]
        )

    def multi_query(self):
        self.response_list = []

        # if max_requested items is less or eq to default page size
        if self.max_items <= WAITROSE_MAX_REQUEST_SIZE:
            self.response_list.append(
                self.query(
                    search_term=self.search_term,
                    start=1,
                    size=self.max_items,
                )
            )
            return

        # normal requests (>128)
        for i in range(
            min(self.get_total_items(), self.max_items) // WAITROSE_MAX_REQUEST_SIZE + 1
        ):
            self.response_list.append(
                self.query(
                    search_term=self.search_term,
                    start=1 + WAITROSE_MAX_REQUEST_SIZE * i,
                    size=WAITROSE_MAX_REQUEST_SIZE,
                )
            )
        return

    def get_items_as_list(self) -> list:
        res = []
        for response in self.response_list:
            res += response.json()["componentsAndProducts"]
        print(
            f"Successfully retrieved {len(res)} items. You requested a maximum of {self.max_items} (default:5000)"
        )
        return res
