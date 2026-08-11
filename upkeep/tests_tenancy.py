"""Cross-account isolation.

Account is the tenant boundary and every scoped view reaches it through
Location, so these assert the boundary directly rather than trusting the
per-view filters to stay correct.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from common.models import Account, Profile

from .models import Item, Location, Task

User = get_user_model()


class CrossAccountIsolationTests(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user(username="alice", password="password")
        self.account_a = Account.objects.create(name="A Household", owner=self.owner_a)
        Profile.objects.create(user=self.owner_a, account=self.account_a)
        self.location_a = Location.objects.create(
            name="A Home", account=self.account_a, default=True
        )
        self.item_a = Item.objects.create(name="AAA-SECRET-ITEM", location=self.location_a)
        self.task_a = Task.objects.create(
            name="AAA-SECRET-TASK",
            item=self.item_a,
            frequency=Task.Frequency.WEEKLY,
        )

        self.owner_b = User.objects.create_user(username="bob", password="password")
        self.account_b = Account.objects.create(name="B Household", owner=self.owner_b)
        Profile.objects.create(user=self.owner_b, account=self.account_b)
        self.location_b = Location.objects.create(
            name="B Home", account=self.account_b, default=True
        )

        self.client = Client()
        self.client.login(username="bob", password="password")

    def test_list_views_do_not_leak_other_accounts_data(self):
        for url in ("item-list", "task-management-list", "task-due-list"):
            with self.subTest(view=url):
                response = self.client.get(reverse(url))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "AAA-SECRET-ITEM")
                self.assertNotContains(response, "AAA-SECRET-TASK")

    def test_reading_another_accounts_object_is_404(self):
        cases = [
            ("item-update", self.item_a.pk),
            ("task-update", self.task_a.pk),
            ("task-delete", self.task_a.pk),
            ("switch-location", self.location_a.pk),
        ]
        for name, pk in cases:
            with self.subTest(view=name):
                response = self.client.get(reverse(name, args=[pk]))
                self.assertEqual(response.status_code, 404)

    def test_mutating_another_accounts_object_is_404(self):
        cases = [
            ("item-delete", self.item_a.pk),
            ("item-archive", self.item_a.pk),
            ("item-update", self.item_a.pk),
            ("task-delete", self.task_a.pk),
            ("task-complete", self.task_a.pk),
            ("task-snooze", self.task_a.pk),
            ("location-delete", self.location_a.pk),
            ("location-update", self.location_a.pk),
        ]
        for name, pk in cases:
            with self.subTest(view=name):
                response = self.client.post(reverse(name, args=[pk]), {})
                self.assertEqual(response.status_code, 404)

        # Nothing was actually mutated or removed.
        self.item_a.refresh_from_db()
        self.task_a.refresh_from_db()
        self.assertEqual(self.item_a.status, Item.ItemStatus.ACTIVE)
        self.assertIsNone(self.task_a.last_performed)
        self.assertIsNone(self.task_a.snoozed_until)
        self.assertTrue(Location.objects.filter(pk=self.location_a.pk).exists())

    def test_cannot_switch_to_another_accounts_location(self):
        self.client.get(reverse("switch-location", args=[self.location_a.pk]))
        self.assertNotEqual(
            self.client.session.get("active_location_id"), self.location_a.pk
        )

    def test_task_item_dropdown_excludes_other_accounts_items(self):
        response = self.client.get(reverse("task-create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "AAA-SECRET-ITEM")


class AccountlessUserTests(TestCase):
    """Location.account is nullable, so `account=None` filters match orphaned rows.

    A user without a household must not inherit those.
    """

    def setUp(self):
        self.orphan_location = Location.objects.create(name="Orphan", account=None)
        self.orphan_item = Item.objects.create(
            name="ORPHAN-SECRET-ITEM", location=self.orphan_location
        )

        self.user = User.objects.create_user(username="nohousehold", password="password")
        self.client = Client()
        self.client.login(username="nohousehold", password="password")

    def test_scoped_views_redirect_instead_of_exposing_orphaned_data(self):
        for name in ("item-list", "task-management-list", "task-due-list"):
            with self.subTest(view=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(response, reverse("settings-view"))

    def test_cannot_mutate_orphaned_objects(self):
        response = self.client.post(reverse("item-delete", args=[self.orphan_item.pk]))
        self.assertRedirects(response, reverse("settings-view"))
        self.assertTrue(Item.objects.filter(pk=self.orphan_item.pk).exists())

    def test_settings_view_stays_reachable(self):
        response = self.client.get(reverse("settings-view"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "ORPHAN-SECRET-ITEM")
