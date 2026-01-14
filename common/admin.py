from django.contrib import admin
from .models import Account, Profile

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__username")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "account", "full_name")
    search_fields = ("user__username", "full_name")