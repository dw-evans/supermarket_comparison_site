from utils.query import *
from utils.main import *

from pathlib import Path


from utils.query import WaitroseRequest, AsdaRequest
from utils.query import run_and_pickle_request, open_those_pickles

SKIP_LIVE_REQUESTS = True


def test_site_query_pickling():
    # consider turning skip on to prevent spamming the websites with data
    if SKIP_LIVE_REQUESTS:
        assert True
    # disabled at the moment for

    run_and_pickle_request("oats")
    waitrose = open_those_pickles()

    assert type(waitrose.get_items_as_list()) == list


class TestWaitroseRequest:
    def test_multi_query(self):
        if SKIP_LIVE_REQUESTS:
            assert True
        obj = WaitroseRequest(search_term="oats", max_items=10)
        assert len(obj.get_items_as_list()) == 10
