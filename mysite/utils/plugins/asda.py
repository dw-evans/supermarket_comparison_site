from __future__ import annotations

import aenum

import re
import requests

from ..datatypes import *

from ..datatypes import Currency, Price
from ..datatypes import Unit, Quantity


from ..searchrequest import GrocerySearchRequest


from ..store import Store, StoreUnitMap


s = "asda"
# regster the store name in in the enum
aenum.extend_enum(Store, s.upper(), s.lower())

s = Store.ASDA
# register the store's unit map
aenum.extend_enum(
    StoreUnitMap,
    s.value.upper(),
    (
        s,
        {
            "l": Unit.L,
            "kg": Unit.KG,
            "g": Unit.G,
            "pk": Unit.PCS,
        },
    ),
)


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
            unit = Unit(StoreUnitMap(Store.ASDA).unit_dict[qty_info[-1]])
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


class AsdaRequest(GrocerySearchRequest):
    """Does a post request to the asda search api, and stores the response.
    effective for any page size"""

    def __init__(self, search_term: str):
        self.query(search_term=search_term)

    def query(self, search_term: str):
        url = "https://groceries.asda.com/api/bff/graphql"

        payload = {
            "requestorigin": "gi",
            "contract": "web/cms/search",
            "variables": {
                "user_segments": [
                    "1259",
                    "1194",
                    "1140",
                    "1141",
                    "1182",
                    "1130",
                    "1128",
                    "1124",
                    "1126",
                    "1119",
                    "1123",
                    "1117",
                    "1112",
                    "1116",
                    "1109",
                    "1111",
                    "1102",
                    "1110",
                    "1097",
                    "1105",
                    "1100",
                    "1107",
                    "1098",
                    "1038",
                    "1087",
                    "1099",
                    "1070",
                    "1082",
                    "1067",
                    "1047",
                    "1059",
                    "1057",
                    "1055",
                    "1053",
                    "1043",
                    "1041",
                    "1042",
                    "1027",
                    "1023",
                    "1024",
                    "1020",
                    "1019",
                    "1007",
                    "1242",
                    "1241",
                    "1262",
                    "1239",
                    "1256",
                    "1245",
                    "1237",
                    "1263",
                    "1264",
                    "1233",
                    "1249",
                    "1260",
                    "1247",
                    "1238",
                    "1236",
                    "1227",
                    "1208",
                    "1220",
                    "1210",
                    "1172",
                    "1178",
                    "1222",
                    "1231",
                    "1217",
                    "1179",
                    "1225",
                    "1207",
                    "1167",
                    "1221",
                    "1219",
                    "1160",
                    "1180",
                    "1152",
                    "1213",
                    "1206",
                    "1176",
                    "1224",
                    "1165",
                    "1159",
                    "1209",
                    "1169",
                    "1144",
                    "1214",
                    "1177",
                    "1216",
                    "1196",
                    "1173",
                    "1186",
                    "1147",
                    "1183",
                    "1204",
                    "1174",
                    "1191",
                    "1201",
                    "1202",
                    "1190",
                    "1157",
                    "1198",
                    "1189",
                    "1166",
                    "1197",
                    "1150",
                    "1170",
                    "1184",
                    "1271",
                    "1278",
                    "1279",
                    "1269",
                    "1283",
                    "1284",
                    "1285",
                    "1288",
                    "dp-false",
                    "wapp",
                    "store_4565",
                    "vp_L",
                    "anonymous",
                    "clothing_store_enabled",
                    "checkoutOptimization",
                    "NAV_UI",
                    "T003",
                    "T014",
                    "rmp_enabled_user",
                ],
                "is_eat_and_collect": False,
                "store_id": "4565",
                "type": "search",
                "page_size": 1000,
                "page": 1,
                "request_origin": "gi",
                # "ship_date": 1669939200000,
                "payload": {
                    "filter_query": [],
                    "cacheable": True,
                    "keyword": search_term,
                    "personalised_search": False,
                    "tag_past_purchases": True,
                    "page_meta_info": True,
                },
            },
        }
        headers = {"content-type": "application/json", "request-origin": "gi"}

        self.response = requests.request("POST", url, json=payload, headers=headers)

    def get_total_items(self):
        return self.response.json()["data"]["tempo_cms_content"]["zones"][1]["configs"][
            "total_records"
        ]

    def get_items_as_list(self):
        return self.response.json()["data"]["tempo_cms_content"]["zones"][1]["configs"][
            "products"
        ]["items"]
