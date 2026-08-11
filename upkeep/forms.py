from typing import ClassVar

from django import forms

from .models import Item, Location, Task, max_purchase_year


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields: ClassVar = [
            "name",
            "address",
            "zip_code",
            "city",
            "country_code",
        ]
        widgets: ClassVar = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "country_code": forms.TextInput(
                attrs={"class": "form-control", "maxlength": 2}
            ),
        }


class ItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)
        if account:
            self.fields["location"].queryset = Location.objects.filter(account=account)

    class Meta:
        model = Item
        fields: ClassVar = [
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

        widgets: ClassVar = {
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
                    "max": max_purchase_year(),
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


class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)
        if account:
            self.fields["item"].queryset = Item.objects.filter(location__account=account)

    def clean_description(self):
        description = self.cleaned_data.get("description")
        if description:
            if "## Tools & Parts" not in description:
                raise forms.ValidationError(
                    "Description must contain the header '## Tools & Parts'"
                )
            if "## Steps" not in description:
                raise forms.ValidationError(
                    "Description must contain the header '## Steps'"
                )
        return description

    class Meta:
        model = Task
        fields: ClassVar = [
            "name",
            "description",
            "item",
            "frequency",
            "estimated_hours_to_complete",
            "next_due_date",
        ]
        widgets: ClassVar = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": "## Tools & Parts\n- Hammer\n- Nails\n\n## Steps\n1. Step one\n2. Step two",
                }
            ),
            "item": forms.Select(attrs={"class": "form-select"}),
            "frequency": forms.Select(attrs={"class": "form-select"}),
            "estimated_hours_to_complete": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "next_due_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
        help_texts: ClassVar = {
            "description": "Required format: Must include '## Tools & Parts' and '## Steps' headers."
        }
