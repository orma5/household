"""Uploads are served by the app, so the /media/ route carries its own access control."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class MediaServingTests(TestCase):
    """Writes into the configured MEDIA_ROOT — settings.test points it at a temp dir.

    The route's document_root is bound when the URLConf is imported, so
    override_settings(MEDIA_ROOT=...) would not reach it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.receipt = Path(settings.MEDIA_ROOT) / "receipts" / "receipt.pdf"
        cls.receipt.parent.mkdir(parents=True, exist_ok=True)
        cls.receipt.write_bytes(b"%PDF-1.4 receipt bytes")

    @classmethod
    def tearDownClass(cls):
        cls.receipt.unlink(missing_ok=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="password")
        self.client = Client()

    def test_anonymous_request_is_sent_to_login(self):
        response = self.client.get("/media/receipts/receipt.pdf")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_authenticated_request_gets_the_file(self):
        self.client.login(username="viewer", password="password")
        response = self.client.get("/media/receipts/receipt.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"%PDF-1.4 receipt bytes")

    def test_missing_file_is_404_not_an_error(self):
        self.client.login(username="viewer", password="password")
        response = self.client.get("/media/receipts/nope.pdf")
        self.assertEqual(response.status_code, 404)

    def test_path_traversal_does_not_escape_media_root(self):
        self.client.login(username="viewer", password="password")
        for attempt in (
            "/media/../settings/common.py",
            "/media/....//settings/common.py",
            "/media/receipts/../../manage.py",
        ):
            with self.subTest(path=attempt):
                response = self.client.get(attempt)
                self.assertNotEqual(response.status_code, 200)
