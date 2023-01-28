from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect

from dataclasses import dataclass, field

import utils.main

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

from utils.main import Store

from utils.main import WaitroseRequest, WaitroseItem
from utils.main import AsdaRequest, AsdaItem

from utils.main import ItemListFilter, SearchResult

from utils.search import Sorter, SorterEnum, Filter, SearchEnum

import utils.plugins.waitrose
import utils.plugins.asda


utils.plugins.asda.register()

utils.plugins.waitrose.register()


# should perhaps store this in the store enum...
STORE_DISPLAY_INFO = {
    Store.ASDA: {
        "site_name": "asda.com",
    },
    Store.WAITROSE: {
        "site_name": "waitrose.com",
    },
}


class CartItem:
    def __init__(self, item_obj: Item, pcs: int = 0) -> None:
        self.item_obj = item_obj
        self.pcs = pcs
        self.__post_init__()

    def __post_init__(self):
        print(f"self.identifier={self.identfier}")

    @property
    def total_value(self):
        return self.item_obj.price * self.pcs

    @property
    def store(self):
        return self.item_obj.store

    @property
    def description(self):
        return self.item_obj.description

    @property
    def price(self):
        return self.item_obj.price

    @property
    def quantity(self):
        return self.item_obj.quantity

    @property
    def thumbnail(self):
        return self.item_obj.thumbnail

    @property
    def is_null(self):
        return self.item_obj.is_null

    @property
    def unit_price(self):
        return self.item_obj.unit_price

    @property
    def identfier(self):
        # be aware that this doesn't actuall work in DTL
        print(f"getting item object id={self.item_obj.identifier}")
        return self.item_obj.identifier


@dataclass
class Cart:
    items: list[CartItem] = field(default_factory=list)

    @property
    def total_value(self) -> Price:
        return sum(i.total_value for i in self.items)

    @property
    def n_items(self):
        return len(self.items)

    def clear_items(self):
        self.items = []


# @dataclass
class ShopSession:
    def __init__(self, store: Store):
        self.store: Store = store
        self.query: str = ""
        self.max_items: int = 5
        self.items: list[Item] = []

        self.search_result: SearchResult = SearchResult([])
        self.cart: Cart = Cart()

        # self.unit_type_filter = Filter.UnitTypeFilter(
        #     [

        #     ]
        # )

        self.filter: ItemListFilter = ItemListFilter()

        # for f in self.filter.filters._filters_as_list():
        #     if f.__name__ == "unit_type_filter":
        #         f.enable()

        self.filter.filters.unit_type_filter.enable()

    @property
    def site_name(self):
        return STORE_DISPLAY_INFO[self.store]["site_name"]

    @property
    def cart_items(self):
        return self.cart.items

    @property
    def item_list_displayed(self):
        self.search_result.filter_and_sort(self.filter)
        # slightly dodgey
        return self.search_result._sorted_and_filtered_list

    def add_item_to_cart_by_id(self, item_identifier: str):
        filter_result = list(
            filter(
                lambda x: str(x.identifier) == item_identifier,
                self.search_result.initial_list,
            )
        )
        if len(filter_result) == 1:

            item = filter_result[0]

            # crudely ignore doubling adds to cart
            if item not in [cart_item.item_obj for cart_item in self.cart_items]:
                print(f"adding id={item_identifier} to cart")
                self.cart_items.append(CartItem(item, pcs=1))

            else:
                filter_result = list(
                    filter(
                        lambda cart_item: str(cart_item.item_obj.identifier)
                        == item_identifier,
                        self.cart_items,
                    )
                )
                if len(filter_result) > 0:
                    cart_item = filter_result[0]
                    cart_item.pcs += 1

    def remove_item_from_cart_by_id(self, item_identifier: str):
        # make sure to get the uuid as a string
        filter_result = list(
            filter(
                lambda x: str(x.item_obj.identifier) == item_identifier, self.cart_items
            )
        )

        if len(filter_result) > 0:

            item = filter_result[0]

            # crudely ignore doubling adds to cart
            if item in self.cart_items:
                if item.pcs > 1:
                    item.pcs -= 1
                else:
                    self.cart_items.remove(item)


class GlobalSession:
    def __init__(self):
        self.shop_sessions = [
            ShopSession(Store.WAITROSE),
            ShopSession(Store.ASDA),
            # ShopSession(Store.WAITROSE),
        ]

    @property
    def s_list(self):
        return self.shop_sessions

    def get_shop_session_by_store(self, store: Store) -> ShopSession:
        return list(filter(lambda x: x.store == store, self.shop_sessions))[0]


# hacky price converter to display in templates
def to_nzd(obj: Price):
    return obj.convert_to(Currency.NZD)


setattr(Price, "to_nzd", to_nzd)


g = GlobalSession()


def home(request):

    # for s in g.s_list:

    if request.method == "GET":

        print(request.GET)

        # handle a search query
        if "q" in request.GET:

            for s in g.s_list:

                # save the search query
                s.query = request.GET.get("q")

                items = [
                    SearchEnum(s.store).item_class(item)
                    for item in SearchEnum(s.store)
                    .search_request_class(s.query, max_items=s.max_items)
                    .get_items_as_list()
                ]

                items = [item for item in items if not item.is_null]

                s.search_result = SearchResult(items)

    if request.method == "POST":
        print(request.POST)

        if "add_to_cart" in request.POST:
            val: str = request.POST.get("add_to_cart")
            store_value, item_id = val.split("_")

            s = g.get_shop_session_by_store(Store(store_value))

            s.add_item_to_cart_by_id(item_id)

            # s.add_item_to_cart_by_id(request.POST.get("add_to_cart"))

        if "remove_from_cart" in request.POST:
            val: str = request.POST.get("remove_from_cart")
            store_value, item_id = val.split("_")

            s = g.get_shop_session_by_store(Store(store_value))
            s.remove_item_from_cart_by_id(request.POST.get("remove_from_cart"))

        if "sort_by" in request.POST:
            for s in g.s_list:
                s.filter.sorter = Sorter(SorterEnum(request.POST.get("sort_by")))

        if "filter_by" in request.POST:
            filter_by_val = request.POST.get("filter_by")

            for s in g.s_list:
                # print(f"UnitType(filter_by_val)={UnitType(filter_by_val)}")
                # s.unit_type_filter.toggle_unit_type_accept_list(UnitType(filter_by_val))

                print(f"filter-object-before-click={s.filter.filters.unit_type_filter}")
                print(f"clicked={UnitType(filter_by_val)}")

                s.filter.filters.unit_type_filter.toggle_unit_type_accept_list(
                    UnitType(filter_by_val)
                )
                print(
                    f"store={s.store} unittypes_accepted={s.filter.filters.unit_type_filter.unit_type_accept_list}"
                )

        if "clear_filters" in request.POST:
            for s in g.s_list:
                s.filter.clear_filters()
            # s.filter.clear_filters()
            pass

        if "clear_cart" in request.POST:
            val = request.POST.get("clear_cart")
            g.get_shop_session_by_store(Store(val)).cart.clear_items()

    else:
        pass

    context = {
        "g": g,
    }

    return render(
        request=request,
        template_name="shopping/home.html",
        context=context,
    )
