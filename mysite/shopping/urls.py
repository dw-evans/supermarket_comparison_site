from django.urls import path
from . import views


app_name = "shopping"
urlpatterns = [
    path("", views.home, name="home"),
    # path("add_to_cart/<slug:item_identifier>", views.add_to_cart, name="add_to_cart"),
    # path(
    #     "remove_from_cart/<slug:item_identifier>",
    #     views.remove_from_cart,
    #     name="remove_from_cart",
    # ),
]
