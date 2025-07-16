from django.urls import path
from . import views

urlpatterns = [
    path("overview/", views.maintenance_list, name="maintenance-list"),
    path("items/", views.item_list, name="item-list"),
]
