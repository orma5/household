from django.urls import path
from . import views

urlpatterns = [
    path("overview/", views.maintenance_list, name="maintenance-list"),
    path("items/", views.item_list, name="item-list"),
    path("items/<int:pk>/detail/", views.item_detail, name="item_detail"),
]
