from typing import ClassVar

from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields: ClassVar = ["full_name", "profile_picture"]
        widgets: ClassVar = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "profile_picture": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }
