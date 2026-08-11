"""Active-location resolution and the regressions around it.

All the scoped views share `selectors.get_active_location`, so the fallback and
session-repair behaviour is asserted here once rather than per view.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from common.models import Account, Profile

from .models import Item, Location

User = get_user_model()


class ActiveLocationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="resident", password="password")
        self.account = Account.objects.create(name="Household", owner=self.user)
        Profile.objects.create(user=self.user, account=self.account)

        self.default_location = Location.objects.create(
            name="Main House", account=self.account, default=True
        )
        self.other_location = Location.objects.create(
            name="Cabin", account=self.account
        )
        self.default_item = Item.objects.create(
            name="DEFAULT-LOC-ITEM", location=self.default_location
        )
        self.other_item = Item.objects.create(
            name="OTHER-LOC-ITEM", location=self.other_location
        )

        self.client = Client()
        self.client.login(username="resident", password="password")

    def test_falls_back_to_default_location_and_records_it(self):
        response = self.client.get(reverse("item-list"))
        self.assertContains(response, "DEFAULT-LOC-ITEM")
        self.assertNotContains(response, "OTHER-LOC-ITEM")
        self.assertEqual(
            self.client.session["active_location_id"], self.default_location.id
        )

    def test_stale_session_location_falls_back_instead_of_showing_nothing(self):
        """A deleted location used to leave the list empty while the nav showed the default."""
        session = self.client.session
        session["active_location_id"] = self.other_location.id
        session.save()
        self.other_location.delete()

        response = self.client.get(reverse("item-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DEFAULT-LOC-ITEM")
        self.assertEqual(
            self.client.session["active_location_id"], self.default_location.id
        )

    def test_switching_location_scopes_the_item_list(self):
        self.client.get(reverse("switch-location", args=[self.other_location.pk]))
        response = self.client.get(reverse("item-list"))
        self.assertContains(response, "OTHER-LOC-ITEM")
        self.assertNotContains(response, "DEFAULT-LOC-ITEM")

    def test_item_list_query_count_is_independent_of_item_count(self):
        """Each item renders an edit form; those must not each re-query locations."""
        self.client.get(reverse("item-list"))  # prime the session

        with CaptureQueriesContext(connection) as baseline:
            self.client.get(reverse("item-list"))

        for i in range(30):
            Item.objects.create(name=f"Filler {i}", location=self.default_location)

        with CaptureQueriesContext(connection) as scaled:
            self.client.get(reverse("item-list"))

        self.assertEqual(len(scaled), len(baseline))


class ViewRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="regress", password="password")
        self.account = Account.objects.create(name="Household", owner=self.user)
        Profile.objects.create(user=self.user, account=self.account)
        self.location = Location.objects.create(
            name="Main House", account=self.account, default=True
        )
        self.item = Item.objects.create(name="Toaster", location=self.location)

        self.client = Client()
        self.client.login(username="regress", password="password")

    def test_item_update_get_renders(self):
        """The view pointed at a template name that does not exist on disk."""
        response = self.client.get(reverse("item-update", args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_item_update_invalid_post_renders_instead_of_erroring(self):
        response = self.client.post(
            reverse("item-update", args=[self.item.pk]), {"name": ""}
        )
        self.assertEqual(response.status_code, 200)


class MissingProfileTests(TestCase):
    """Users created outside the signup flow (admin, createsuperuser) have no Profile."""

    def setUp(self):
        self.user = User.objects.create_user(username="profileless", password="password")
        self.account = Account.objects.create(name="Household", owner=self.user)
        self.client = Client()
        self.client.login(username="profileless", password="password")

    def test_pages_do_not_error_without_a_profile(self):
        self.assertFalse(Profile.objects.filter(user=self.user).exists())

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("settings-view"))
        self.assertEqual(response.status_code, 200)

        self.assertTrue(Profile.objects.filter(user=self.user).exists())
