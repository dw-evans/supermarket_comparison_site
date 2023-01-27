from __future__ import annotations
from abc import ABC, abstractmethod


class GrocerySearchRequest(ABC):
    def __init__(self):
        print(f"Initializing GrocerySearchRequest...")
        pass

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


import pickle
from pathlib import Path


def to_pickle(data, fpath) -> None:
    # writes data to a pkl file
    with open(fpath, "wb+") as f:
        pickle.dump(data, f)


def open_pickle(fpath):
    # opens data from a binary pkl file
    with open(fpath, "rb") as f:
        data = pickle.load(f)
    return data


def run_and_pickle_request(search_term, max_items=20):
    from waitrose import WaitroseRequest

    # a test to run a search request on multiple supermarkets and store the result in a pickle
    # idea being to not spam servers or to store a test dataset.

    b = WaitroseRequest(search_term=search_term, max_items=max_items)

    path2 = Path(__file__).parent / "pkl/waitrose.pkl"
    to_pickle(b, path2)

    # a = AsdaRequest(search_term=search_term)

    # path1 = Path(__file__).parent / "pkl/asda.pkl"
    # to_pickle(a, path1)


def open_those_pickles() -> "pkl":
    # opening the pickles from run and pickle request.
    path2 = Path(__file__).parent / "pkl/waitrose.pkl"

    waitrose = open_pickle(path2)

    return waitrose
