from django.urls import path
from . import views

urlpatterns = [
    path("", views.maintenance_list, name="maintenance-list"),
]
