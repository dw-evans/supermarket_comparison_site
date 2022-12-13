from django.urls import path
from . import views


app_name = "shopping"
urlpatterns = [
    path("index", views.index, name="index"),
    path("search/<slug:search_string>", views.search, name="search"),
]
