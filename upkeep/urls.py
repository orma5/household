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
    path("locations/switch/<int:pk>/", views.switch_location, name="switch-location"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location-delete"),
    path("locations/<int:pk>/update/", views.location_update, name="location-update"),
    # Task Management
    path("tasks/due/", views.task_due_list, name="task-due-list"),
    path("maintenance/", views.task_management_list, name="task-management-list"),
    path("tasks/create/", views.task_create, name="task-create"),
    path("tasks/<int:pk>/update/", views.task_update, name="task-update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task-delete"),
    path("tasks/<int:pk>/complete/", views.task_complete, name="task-complete"),
    path("tasks/<int:pk>/snooze/", views.task_snooze, name="task-snooze"),
]
