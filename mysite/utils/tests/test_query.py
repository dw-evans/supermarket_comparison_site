from utils.query import *
from utils.main import *

from pathlib import Path


from utils.query import WaitroseRequest, AsdaRequest
from utils.query import run_and_pickle_request, open_those_pickles


def test_site_query_pickling():

    run_and_pickle_request("oats")
    waitrose = open_those_pickles()

    assert type(waitrose.get_items_as_list()) == list


class TestWaitroseRequest:
    def test_multi_query(self):
        obj = WaitroseRequest(search_term="oats", max_items=10)
        assert len(obj.get_items_as_list()) == 10
