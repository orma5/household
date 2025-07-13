# upkeep/forms.py
from django import forms
from .models import Task, Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "location", "sub_location", "purchase_year", "initial_value"]


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "name",
            "description",
            "frequency",
            "item",
            "last_performed",
            "next_due_date",
        ]
        widgets = {
            "last_performed": forms.DateInput(attrs={"type": "date"}),
            "next_due_date": forms.DateInput(attrs={"type": "date"}),
        }
