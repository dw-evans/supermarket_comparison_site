from django.shortcuts import render


from utils.site_query import run_and_pickle_request, open_those_pickles
from utils.site_query import WaitroseRequest, AsdaRequest
from utils.main import WaitroseItem


def index(request):

    # run_and_pickle_request("milk")

    # asda, waitrose = open_those_pickles()

    item_list = [
        WaitroseItem(item) for item in WaitroseRequest("milk").get_items_as_list()
    ]

    context = {
        "item_list": [item for item in item_list if not item.is_null],
        "null_item_list": [item for item in item_list if item.is_null],
    }

    return render(request=request, template_name="shopping/index.html", context=context)


def search(request, search_string):

    item_list = [
        WaitroseItem(item)
        for item in WaitroseRequest(search_string).get_items_as_list()
    ]

    context = {
        "search_term": search_string,
        "item_list": [item for item in item_list if not item.is_null],
        "null_item_list": [item for item in item_list if item.is_null],
    }

    return render(
        request=request, template_name="shopping/search.html", context=context
    )
