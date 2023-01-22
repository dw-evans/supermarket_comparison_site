from django.shortcuts import render

from utils.query import run_and_pickle_request, open_those_pickles
from utils.query import WaitroseRequest, AsdaRequest
from utils.main import Item, WaitroseItem

from utils.main import ItemListFilter, SorterEnum
from utils.main import QuantityFilter
from utils.main import PriceFilter, PriceSorter

from dataclasses import dataclass

# query = ""
# items = []
# cart_items = []

from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect


@dataclass
class Session:
    query: str
    items: list[Item]
    cart_items: list[Item]


s = Session(query="", items=[], cart_items=[])


def query(request, query_string):

    return HttpResponse(f"query={query_string}")


def home(request):

    print(request)

    if request.method == "POST":

        # print(request.headers)
        # print(request.POST)

        # handle a search query
        if "query" in request.POST:

            s.query = request.POST["query"]

            items = [
                WaitroseItem(item)
                for item in WaitroseRequest(s.query, max_items=20).get_items_as_list()
            ]

            items = [item for item in items if not item.is_null]

            # default to sorting by highest price
            filter = ItemListFilter(
                initial_list=items,
                sorter=PriceSorter(SorterEnum.HIGHEST_PRICE),
                filters=[],
            )

            items = filter.get_new_list(items)
            s.items = items

        # handle a filter form need to improve
        if "price_filter_low" in request.POST:
            print("filtersyep")

            # Todo add enums for all filter cases jesus

            filter = ItemListFilter(
                initial_list=items,
                sorter=PriceSorter(SorterEnum.LOWEST_UNIT_PRICE),
                filters=[],
            )

            items = filter.get_new_list(items)

            context = {
                # "search_term": query,
                "item_list": items,
            }

    else:
        pass

    context = {
        "search_term": s.query,
        "item_list": s.items,
        "cart_item_list": s.cart_items,
    }

    return render(
        request=request,
        template_name="shopping/home.html",
        context=context,
    )


def add_to_cart(request, item_identifier):

    # make sure to get the uuid as a string
    filter_result = list(
        filter(lambda x: str(x.identifier) == item_identifier, s.items)
    )

    print(f"len(filter_result)={len(filter_result)}")
    if len(filter_result) == 1:

        item = filter_result[0]

        # crudely ignore doubling adds to cart
        if item not in s.cart_items:
            print(f"adding id={item_identifier} to cart")
            s.cart_items.append(item)
        else:
            s.cart_items.append(item)
            pass
            # res: CartItem = next((i for i in s.cart_items == item), None)
            # res.pieces += 1
            # print(res.pieces)

    return HttpResponseRedirect(reverse("shopping:home"))


def remove_from_cart(request, item_identifier):

    # make sure to get the uuid as a string
    filter_result = list(
        filter(lambda x: str(x.identifier) == item_identifier, s.cart_items)
    )

    if len(filter_result) > 0:

        item = filter_result[0]

        # crudely ignore doubling adds to cart
        if item in s.cart_items:
            s.cart_items.remove(item)

    return HttpResponseRedirect(reverse("shopping:home"))
