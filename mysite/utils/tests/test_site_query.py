from utils.site_query import WaitroseRequest, AsdaRequest
from utils.site_query import run_and_pickle_request, open_those_pickles
from pathlib import Path


def test_site_query_pickling():
    run_and_pickle_request("oats")

    asda, waitrose = open_those_pickles()

    assert (type(asda.get_items_as_list()) == list) and (
        type(waitrose.get_items_as_list()) == list
    )
