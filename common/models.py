from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, editable=False
    )

    class Meta:
        abstract = True


class Account(BaseModel):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_accounts"
    )

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="members"
    )
    full_name = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )

    def __str__(self):
        return f"Profile for {self.user.username}"


def get_profile(user):
    """Return the user's Profile, creating it if missing.

    Users can be created without a Profile (via the admin, createsuperuser, or
    a fixture), and every account-scoped view needs one. Creating on demand
    here keeps those users out of a 500 on `user.profile`.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def get_account(user):
    """Return the Account the user belongs to, or None if they have no household yet."""
    return get_profile(user).account
