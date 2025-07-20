# inventory/forms.py

from django import forms
from .models import Item
import datetime


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            # Required
            "name",
            "location",
            "quantity",
            # Optional
            "area",
            "brand",
            "model_number",
            "serial_number",
            "purchase_value",
            "purchase_place",
            "purchase_year",
            "warranty_expiration",
            "receipt_file",
            "notes",
            "manufacturer_manual_url",
            "end_of_service_date",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "area": forms.TextInput(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "model_number": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "purchase_value": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "purchase_place": forms.TextInput(attrs={"class": "form-control"}),
            "purchase_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1900,
                    "max": datetime.datetime.now().year + 1,
                }
            ),
            "warranty_expiration": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_of_service_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "receipt_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "manufacturer_manual_url": forms.URLInput(attrs={"class": "form-control"}),
        }
