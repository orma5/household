from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.upkeep_view, name="upkeep-list"),
]
