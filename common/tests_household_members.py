"""Household creation, renaming, and membership via the settings page.

These pin the behaviour of the POST branches in settings_view so it can be
restructured without silently changing what it does.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from common.models import Account, Profile

User = get_user_model()


class HouseholdLifecycleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="password")
        self.client = Client()
        self.client.login(username="owner", password="password")

    def test_creating_a_household_links_it_to_the_profile(self):
        Profile.objects.create(user=self.user, account=None)

        response = self.client.post(
            reverse("settings-view"),
            {"create_household": "1", "household_name": "The Nest"},
        )
        self.assertRedirects(response, reverse("settings-view"))

        account = Account.objects.get(name="The Nest")
        self.assertEqual(account.owner, self.user)
        self.assertEqual(Profile.objects.get(user=self.user).account, account)

    def test_renaming_a_household(self):
        account = Account.objects.create(name="Old Name", owner=self.user)
        Profile.objects.create(user=self.user, account=account)

        response = self.client.post(
            reverse("settings-view"),
            {"update_household": "1", "household_name": "New Name"},
        )
        self.assertRedirects(response, reverse("settings-view"))
        account.refresh_from_db()
        self.assertEqual(account.name, "New Name")


class AddMemberTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password")
        self.account = Account.objects.create(name="Household", owner=self.owner)
        Profile.objects.create(user=self.owner, account=self.account)
        self.client = Client()
        self.client.login(username="owner", password="password")

    def _messages(self, response):
        return " ".join(str(m) for m in response.context["messages"])

    def test_owner_can_add_a_member(self):
        response = self.client.post(
            reverse("settings-view"),
            {
                "add_member": "1",
                "new_username": "flatmate",
                "new_password": "a-perfectly-fine-password",
                "new_email": "flatmate@example.com",
            },
        )
        self.assertRedirects(response, reverse("settings-view"))

        member = User.objects.get(username="flatmate")
        self.assertEqual(member.email, "flatmate@example.com")
        self.assertEqual(Profile.objects.get(user=member).account, self.account)

    def test_non_owner_cannot_add_a_member(self):
        other = User.objects.create_user(username="member", password="password")
        Profile.objects.create(user=other, account=self.account)

        self.client.login(username="member", password="password")
        response = self.client.post(
            reverse("settings-view"),
            {
                "add_member": "1",
                "new_username": "intruder",
                "new_password": "a-perfectly-fine-password",
            },
        )
        self.assertRedirects(response, reverse("settings-view"))
        self.assertFalse(User.objects.filter(username="intruder").exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="taken", password="password")

        response = self.client.post(
            reverse("settings-view"),
            {
                "add_member": "1",
                "new_username": "taken",
                "new_password": "a-perfectly-fine-password",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", self._messages(response))
        self.assertEqual(User.objects.filter(username="taken").count(), 1)

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            reverse("settings-view"),
            {"add_member": "1", "new_username": "newbie", "new_password": "123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self._messages(response))
        self.assertFalse(User.objects.filter(username="newbie").exists())
