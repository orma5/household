from django.contrib import admin
from .models import Item, Task, Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "default")
    list_filter = ("account", "default")

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "status")
    list_filter = ("location__account", "status", "location")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "item", "frequency", "next_due_date")
    list_filter = ("item__location__account", "frequency")
