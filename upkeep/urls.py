from django.urls import path
from . import views

urlpatterns = [
    path("overview/", views.maintenance_list, name="maintenance-list"),
    path("items/", views.item_list, name="item-list"),
    path("items/create/", views.item_create, name="item-create"),
    path("items/<int:pk>/delete/", views.item_delete, name="item-delete"),
    path("items/<int:pk>/update/", views.item_update, name="item-update"),
    path("items/<int:pk>/archive/", views.item_archive, name="item-archive"),
]
