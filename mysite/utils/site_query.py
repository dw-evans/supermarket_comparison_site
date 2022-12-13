from __future__ import annotations

import requests
from abc import ABC, abstractmethod
import pickle
from pathlib import Path


class GrocerySearchRequest(ABC):
    @abstractmethod
    def query(self):
        # main query for search request
        pass

    @abstractmethod
    def get_items_as_list(self) -> list:
        # gets the items as a list, need to have it check all pages
        pass

    @abstractmethod
    def get_total_items(self) -> int:
        # gets the total number of items per the request
        pass


WAITROSE_MAX_REQUEST_SIZE = 128


class WaitroseRequest(GrocerySearchRequest):
    """Does a post request to the waitrose search api and stores the response
    Needs to be modified to handle item lists > 128 per page"""

    def __init__(self, search_term: str):
        self.search_term = search_term
        self.multi_query()
        # self.query(search_term=search_term)

    def query(
        self, search_term: str, start: int, size: int = WAITROSE_MAX_REQUEST_SIZE
    ) -> "httpresponse":
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
        print(self.get_total_items())
        for i in range(self.get_total_items() // WAITROSE_MAX_REQUEST_SIZE + 1):
            print(f"i={i}")
            self.response_list.append(
                self.query(
                    search_term=self.search_term,
                    start=1 + WAITROSE_MAX_REQUEST_SIZE * i,
                )
            )

    def get_items_as_list(self) -> list:
        res = []
        print(f"length of response_list={len(self.response_list)}")
        for response in self.response_list:
            res += response.json()["componentsAndProducts"]
            print(len(response.json()["componentsAndProducts"]))
        return res


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


def to_pickle(data, fpath) -> None:
    # writes data to a pkl file
    with open(fpath, "wb+") as f:
        pickle.dump(data, f)


def open_pickle(fpath):
    # opens data from a binary pkl file
    with open(fpath, "rb") as f:
        data = pickle.load(f)
    return data


def run_and_pickle_request(search_term):
    # a test to run a search request on multiple supermarkets and store the result in a pickle
    # idea being to not spam servers or to store a test dataset.

    a = AsdaRequest(search_term=search_term)

    b = WaitroseRequest(search_term=search_term)

    path1 = Path(__file__).parent / "pkl/asda.pkl"
    to_pickle(a, path1)

    path2 = Path(__file__).parent / "pkl/waitrose.pkl"
    to_pickle(b, path2)


def open_those_pickles():
    # opening the pickles from run and pickle request.
    path1 = Path(__file__).parent / "pkl/asda.pkl"
    path2 = Path(__file__).parent / "pkl/waitrose.pkl"

    asda = open_pickle(path1)
    waitrose = open_pickle(path2)

    return asda, waitrose
