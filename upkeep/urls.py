from django.urls import path
from . import views

urlpatterns = [
    path("", views.upkeep_view, name="upkeep-list"),
    path("create-task/", views.create_task, name="create_task"),
]
