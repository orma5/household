"""The settings page must not swallow a rejected submission.

Every branch there returns 200 on failure, so without feedback the page just
appears to reload having done nothing.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from common.models import Account, Profile

User = get_user_model()


class ProfileFormErrorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="resident", password="password")
        self.account = Account.objects.create(name="Household", owner=self.user)
        Profile.objects.create(
            user=self.user, account=self.account, full_name="Original Name"
        )
        self.client = Client()
        self.client.login(username="resident", password="password")

    def test_too_long_name_is_reported_and_not_saved(self):
        response = self.client.post(
            reverse("settings-view"),
            {"update_profile": "1", "full_name": "x" * 256},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["profile_form"],
            "full_name",
            "Ensure this value has at most 255 characters (it has 256).",
        )
        self.assertEqual(Profile.objects.get(user=self.user).full_name, "Original Name")

    def test_non_image_upload_is_reported(self):
        not_an_image = SimpleUploadedFile(
            "receipt.pdf", b"%PDF-1.4 not an image", content_type="application/pdf"
        )
        response = self.client.post(
            reverse("settings-view"),
            {
                "update_profile": "1",
                "full_name": "Fine",
                "profile_picture": not_an_image,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["profile_form"].errors)

    def test_the_rejected_value_is_shown_back_to_the_user(self):
        """A bound form is useless if the template drops its errors."""
        response = self.client.post(
            reverse("settings-view"),
            {"update_profile": "1", "full_name": "y" * 256},
        )
        self.assertContains(response, "at most 255 characters")

    def test_a_valid_update_still_redirects_and_saves(self):
        response = self.client.post(
            reverse("settings-view"),
            {"update_profile": "1", "full_name": "New Name"},
        )
        self.assertRedirects(response, reverse("settings-view"))
        self.assertEqual(Profile.objects.get(user=self.user).full_name, "New Name")


class HouseholdNameFeedbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="password")
        self.client = Client()
        self.client.login(username="owner", password="password")

    def _messages(self, response):
        return [str(m) for m in response.context["messages"]]

    def test_renaming_to_an_empty_name_says_so(self):
        account = Account.objects.create(name="Household", owner=self.user)
        Profile.objects.create(user=self.user, account=account)

        response = self.client.post(
            reverse("settings-view"), {"update_household": "1", "household_name": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._messages(response))
        account.refresh_from_db()
        self.assertEqual(account.name, "Household")

    def test_creating_with_an_empty_name_says_so(self):
        Profile.objects.create(user=self.user, account=None)

        response = self.client.post(
            reverse("settings-view"), {"create_household": "1", "household_name": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._messages(response))
        self.assertFalse(Account.objects.filter(owner=self.user).exists())
