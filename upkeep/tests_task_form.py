from django.test import TestCase
from .forms import TaskForm
from .models import Item, Location
from common.models import Account
from django.contrib.auth import get_user_model
import datetime

User = get_user_model()

class TaskFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.account = Account.objects.create(name="Test Household", owner=self.user)
        self.location = Location.objects.create(name="Test Location", account=self.account)
        self.item = Item.objects.create(name="Test Item", location=self.location)

    def test_valid_form(self):
        data = {
            "name": "Valid Task",
            "description": "## Tools & Parts\nHammer\n## Steps\nHit it.",
            "item": self.item.pk,
            "frequency": 7,
            "next_due_date": datetime.date.today()
        }
        form = TaskForm(data=data, account=self.account)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_description_missing_headers(self):
        data = {
            "name": "Invalid Task",
            "description": "Just some text",
            "item": self.item.pk,
            "frequency": 7,
            "next_due_date": datetime.date.today()
        }
        form = TaskForm(data=data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn("Description must contain the header '## Tools & Parts'", form.errors["description"])

    def test_invalid_description_missing_steps(self):
        data = {
            "name": "Invalid Task",
            "description": "## Tools & Parts\nStuff",
            "item": self.item.pk,
            "frequency": 7,
            "next_due_date": datetime.date.today()
        }
        form = TaskForm(data=data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn("Description must contain the header '## Steps'", form.errors["description"])
