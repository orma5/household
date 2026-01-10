from django.urls import path
from . import views

urlpatterns = [
    path("items/", views.item_list, name="item-list"),
    path("items/create/", views.item_create, name="item-create"),
    path("items/<int:pk>/delete/", views.item_delete, name="item-delete"),
    path("items/<int:pk>/update/", views.item_update, name="item-update"),
    path("items/<int:pk>/archive/", views.item_archive, name="item-archive"),
    path("settings/", views.settings_view, name="settings-view"),
    path("locations/create/", views.location_create, name="location-create"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location-delete"),
    path("locations/<int:pk>/update/", views.location_update, name="location-update"),
]
