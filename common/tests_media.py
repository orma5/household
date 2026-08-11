"""Uploads are served by the app, scoped to the account that owns them.

Writes into the configured MEDIA_ROOT — settings.test points it at a temp dir.
The view reads settings.MEDIA_ROOT at request time, but these tests keep to the
configured value anyway so the URLConf and the view agree.
"""

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from common.models import Account, Profile
from upkeep.models import Item, Location

User = get_user_model()


def write_upload(relative_path, content=b"file bytes"):
    full = Path(settings.MEDIA_ROOT) / relative_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(content)
    return full


class UploadAccessTests(TestCase):
    """Account A owns a receipt; account B must not be able to fetch it."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="password")
        cls.account_a = Account.objects.create(name="A Household", owner=cls.alice)
        cls.profile_a = Profile.objects.create(
            user=cls.alice,
            account=cls.account_a,
            profile_picture="profile_pictures/alice.jpg",
        )
        location_a = Location.objects.create(
            name="A Home", account=cls.account_a, default=True
        )
        cls.item_a = Item.objects.create(
            name="Fridge", location=location_a, receipt_file="receipts/fridge.pdf"
        )

        # A second member of the same household.
        cls.anna = User.objects.create_user(username="anna", password="password")
        Profile.objects.create(user=cls.anna, account=cls.account_a)

        cls.bob = User.objects.create_user(username="bob", password="password")
        cls.account_b = Account.objects.create(name="B Household", owner=cls.bob)
        Profile.objects.create(user=cls.bob, account=cls.account_b)

    def setUp(self):
        write_upload("receipts/fridge.pdf", b"%PDF-1.4 fridge receipt")
        write_upload("profile_pictures/alice.jpg", b"\xff\xd8\xff alice")
        # Present on disk but referenced by no row.
        write_upload("receipts/orphan.pdf", b"%PDF-1.4 orphan")
        self.client = Client()

    def test_owner_can_fetch_their_receipt(self):
        self.client.login(username="alice", password="password")
        response = self.client.get("/media/receipts/fridge.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join(response.streaming_content), b"%PDF-1.4 fridge receipt"
        )

    def test_household_member_can_fetch_the_receipt(self):
        self.client.login(username="anna", password="password")
        response = self.client.get("/media/receipts/fridge.pdf")
        self.assertEqual(response.status_code, 200)

    def test_other_account_cannot_fetch_the_receipt(self):
        self.client.login(username="bob", password="password")
        response = self.client.get("/media/receipts/fridge.pdf")
        self.assertEqual(response.status_code, 404)

    def test_other_account_cannot_fetch_a_profile_picture(self):
        self.client.login(username="bob", password="password")
        response = self.client.get("/media/profile_pictures/alice.jpg")
        self.assertEqual(response.status_code, 404)

    def test_owner_can_fetch_their_profile_picture(self):
        self.client.login(username="alice", password="password")
        response = self.client.get("/media/profile_pictures/alice.jpg")
        self.assertEqual(response.status_code, 200)

    def test_file_referenced_by_no_row_is_not_served(self):
        self.client.login(username="alice", password="password")
        response = self.client.get("/media/receipts/orphan.pdf")
        self.assertEqual(response.status_code, 404)

    def test_user_without_an_account_gets_nothing(self):
        User.objects.create_user(username="nohousehold", password="password")
        self.client.login(username="nohousehold", password="password")
        response = self.client.get("/media/receipts/fridge.pdf")
        self.assertEqual(response.status_code, 404)

    def test_own_profile_picture_works_without_an_account(self):
        loner = User.objects.create_user(username="loner", password="password")
        Profile.objects.create(
            user=loner, account=None, profile_picture="profile_pictures/loner.jpg"
        )
        write_upload("profile_pictures/loner.jpg", b"\xff\xd8\xff loner")

        self.client.login(username="loner", password="password")
        response = self.client.get("/media/profile_pictures/loner.jpg")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_request_is_sent_to_login(self):
        response = self.client.get("/media/receipts/fridge.pdf")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_missing_file_is_404(self):
        self.client.login(username="alice", password="password")
        response = self.client.get("/media/receipts/nope.pdf")
        self.assertEqual(response.status_code, 404)

    def test_path_traversal_does_not_escape_media_root(self):
        self.client.login(username="alice", password="password")
        for attempt in (
            "/media/../settings/common.py",
            "/media/....//settings/common.py",
            "/media/receipts/../../manage.py",
        ):
            with self.subTest(path=attempt):
                response = self.client.get(attempt)
                self.assertNotEqual(response.status_code, 200)
