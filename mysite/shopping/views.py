from django.shortcuts import render

from utils.query import run_and_pickle_request, open_those_pickles
from utils.query import WaitroseRequest, AsdaRequest
from utils.main import (
    Item,
    WaitroseItem,
    Price,
    Currency,
    Unit,
    UnitPrice,
    Quantity,
    UnitType,
)

from utils.main import ItemListFilter, SorterEnum
from utils.main import Filter, Sorter
from utils.main import SorterEnum

from utils.main import SearchResult


from dataclasses import dataclass, field

from utils.main import Store

# query = ""
# items = []
# cart_items = []

from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect


@dataclass
class ShopSession:
    shop_id: Store

    query: str = ""
    query_result: list[Item] = field(default_factory=list)
    query_filter: ItemListFilter = ItemListFilter()


@dataclass
class CartItem:
    item: Item
    pcs: int = 0

    @property
    def total_value(self):
        return self.item.price * self.pcs


@dataclass
class Cart:
    items: list[CartItem] = field(default_factory=list)

    @property
    def total_value(self) -> Price:
        return sum(i.total_value for i in self.items)


# @dataclass
class Session:
    def __init__(self):
        self.query: str = ""
        self.max_items: int = 100
        self.items: list[Item] = []

        self.search_result: SearchResult = SearchResult([])
        self.cart: Cart = Cart()

        self.unit_type_filter = Filter.UnitTypeFilter()

        self.filter: ItemListFilter = ItemListFilter()

        # for f in self.filter.filters._filters_as_list():
        #     if f.__name__ == "unit_type_filter":
        #         f.enable()

        self.filter.filters.unit_type_filter.enable()

    @property
    def cart_items(self):
        return self.cart.items

    @property
    def item_list_displayed(self):
        self.search_result.filter_and_sort(self.filter)
        # slightly dodgey
        return self.search_result._sorted_and_filtered_list


# hacky price converter to display in templates
def to_nzd(obj: Price):
    return obj.convert_to(Currency.NZD)


setattr(Price, "to_nzd", to_nzd)


def add_item_to_cart_by_id(item_identifier: str):
    filter_result = list(
        filter(
            lambda x: str(x.identifier) == item_identifier, s.search_result.initial_list
        )
    )
    if len(filter_result) == 1:

        item = filter_result[0]

        # crudely ignore doubling adds to cart
        if item not in [cart_item.item for cart_item in s.cart_items]:
            print(f"adding id={item_identifier} to cart")
            s.cart_items.append(CartItem(item, pcs=1))

        else:
            filter_result = list(
                filter(
                    lambda cart_item: str(cart_item.item.identifier) == item_identifier,
                    s.cart_items,
                )
            )
            if len(filter_result) > 0:
                cart_item = filter_result[0]
                cart_item.pcs += 1


def remove_item_from_cart_by_id(item_identifier: str):
    # make sure to get the uuid as a string
    filter_result = list(
        filter(lambda x: str(x.item.identifier) == item_identifier, s.cart_items)
    )

    if len(filter_result) > 0:

        item = filter_result[0]

        # crudely ignore doubling adds to cart
        if item in s.cart_items:
            if item.pcs > 1:
                item.pcs -= 1
            else:
                s.cart_items.remove(item)


s = Session()


def home(request):

    if request.method == "GET":
        print(request.GET)
        # handle a search query
        if "q" in request.GET:

            # save the search query
            s.query = request.GET.get("q")

            # get the waitrose items
            items = [
                WaitroseItem(item)
                for item in WaitroseRequest(
                    s.query, max_items=s.max_items
                ).get_items_as_list()
            ]
            items = [item for item in items if not item.is_null]

            s.search_result = SearchResult(items)

    if request.method == "POST":
        print(request.POST)

        if "add_to_cart" in request.POST:
            add_item_to_cart_by_id(request.POST.get("add_to_cart"))

        if "remove_from_cart" in request.POST:
            remove_item_from_cart_by_id(request.POST.get("remove_from_cart"))

        if "sort_by" in request.POST:
            s.filter.sorter = Sorter(SorterEnum(request.POST.get("sort_by")))

        if "filter_by" in request.POST:
            filter_by_val = request.POST.get("filter_by")
            # print(f"UnitType(filter_by_val)={UnitType(filter_by_val)}")
            # s.unit_type_filter.toggle_unit_type_accept_list(UnitType(filter_by_val))

            s.filter.filters.unit_type_filter.toggle_unit_type_accept_list(
                UnitType(filter_by_val)
            )
            print(s.filter.filters.unit_type_filter.unit_type_accept_list)

        if "clear_filters" in request.POST:
            s.filter.clear_filters()

    else:
        pass

    context = {
        "query": s.query,
        "item_list": s.item_list_displayed,
        "cart_item_list": s.cart_items,
    }

    return render(
        request=request,
        template_name="shopping/home.html",
        context=context,
    )


def add_to_cart(request, item_identifier):

    print(f"searching for {item_identifier}")

    # make sure to get the uuid as a string
    filter_result = list(
        filter(
            lambda x: str(x.identifier) == item_identifier, s.search_result.initial_list
        )
    )

    print(f"len(filter_result)={len(filter_result)}")
    if len(filter_result) == 1:

        item = filter_result[0]

        # crudely ignore doubling adds to cart
        if item not in [cart_item.item for cart_item in s.cart_items]:
            print(f"adding id={item_identifier} to cart")
            s.cart_items.append(CartItem(item, pcs=1))

        else:
            filter_result = list(
                filter(
                    lambda cart_item: str(cart_item.item.identifier) == item_identifier,
                    s.cart_items,
                )
            )
            if len(filter_result) > 0:
                cart_item = filter_result[0]
                cart_item.pcs += 1

    return HttpResponseRedirect(reverse("shopping:home"))


def remove_from_cart(request, item_identifier):

    # make sure to get the uuid as a string
    filter_result = list(
        filter(lambda x: str(x.item.identifier) == item_identifier, s.cart_items)
    )

    if len(filter_result) > 0:

        item = filter_result[0]

        # crudely ignore doubling adds to cart
        if item in s.cart_items:
            if item.pcs > 1:
                item.pcs -= 1
            else:
                s.cart_items.remove(item)

    return HttpResponseRedirect(reverse("shopping:home"))
