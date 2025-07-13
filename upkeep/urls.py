from django.urls import path
from . import views

urlpatterns = [
    path("", views.upkeep_view, name="upkeep-list"),
    path("create-task/", views.create_task, name="create_task"),
    path("items/", views.ItemListView.as_view(), name="item-list"),
    path("items/create/", views.ItemCreateView.as_view(), name="item-create"),
    path("items/<int:pk>/update/", views.ItemUpdateView.as_view(), name="item-update"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item-delete"),
    path("locations/", views.LocationListView.as_view(), name="location-list"),
    path(
        "locations/create/", views.LocationCreateView.as_view(), name="location-create"
    ),
    path(
        "locations/<int:pk>/update/",
        views.LocationUpdateView.as_view(),
        name="location-update",
    ),
    path(
        "locations/<int:pk>/delete/",
        views.LocationDeleteView.as_view(),
        name="location-delete",
    ),
]
