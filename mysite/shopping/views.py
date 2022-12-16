from django.shortcuts import render

from utils.query import run_and_pickle_request, open_those_pickles
from utils.query import WaitroseRequest, AsdaRequest
from utils.main import WaitroseItem

from utils.main import ItemListFilter, SorterEnum
from utils.main import QuantityFilter
from utils.main import PriceFilter, PriceSorter

global items
items = []


def home(request):
    global items
    print(request)

    if request.method == "POST":

        print(request.headers)
        print(request.POST)

        if "query" in request.POST:

            query = request.POST["query"]

            items = [
                WaitroseItem(item)
                for item in WaitroseRequest(query, max_items=20).get_items_as_list()
            ]

            items = [item for item in items if not item.is_null]

            filter = ItemListFilter(
                initial_list=items,
                sorter=PriceSorter(SorterEnum.HIGHEST_PRICE),
                filters=[],
            )

            items = filter.get_new_list(items)

            context = {
                "search_term": query,
                "item_list": items,
            }

            return render(
                request=request,
                template_name="shopping/home.html",
                context=context,
            )

        if "price_filter_low" in request.POST:
            print("filtersyep")

            filter = ItemListFilter(
                initial_list=items,
                sorter=PriceSorter(SorterEnum.LOWEST_PRICE),
                filters=[],
            )

            items = filter.get_new_list(items)

            context = {
                # "search_term": query,
                "item_list": items,
            }

            return render(
                request=request,
                template_name="shopping/home.html",
                context=context,
            )

    else:

        context = {
            "search_term": "no search yet bro",
        }

        return render(
            request=request,
            template_name="shopping/home.html",
            context=context,
        )


# def search(request, search_string):

#     # search_string = request.GET["query"]

#     item_list = [
#         WaitroseItem(item)
#         for item in WaitroseRequest(search_string, max_items=10).get_items_as_list()
#     ]

#     context = {
#         "search_term": search_string,
#         "item_list": [item for item in item_list if not item.is_null],
#         # "null_item_list": [item for item in item_list if item.is_null],
#     }

#     return render(
#         request=request, template_name="shopping/search.html", context=context
#     )
