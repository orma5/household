from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from .models import Location, Item, Task

from common.models import Account, Profile

User = get_user_model()

class TaskManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.account = Account.objects.create(name="Test Household", owner=self.user)
        self.profile = Profile.objects.create(user=self.user, account=self.account)
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        self.location = Location.objects.create(
            name="Test Location",
            user=self.user,
            account=self.account,
            default=True
        )
        
        self.item = Item.objects.create(
            name="Test Item",
            location=self.location,
            user=self.user,
            account=self.account,
            quantity=1,
            status=Item.ItemStatus.ACTIVE
        )
        
        self.task = Task.objects.create(
            name="Test Task",
            item=self.item,
            frequency=Task.Frequency.WEEKLY, # 7 days
            next_due_date=datetime.date.today()
        )

    def test_task_complete(self):
        url = reverse('task-complete', args=[self.task.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302) # Redirects
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.last_performed, timezone.now().date())
        # Next due date should be today + 7 days
        expected_due_date = timezone.now().date() + datetime.timedelta(days=7)
        self.assertEqual(self.task.next_due_date, expected_due_date)

    def test_task_snooze(self):
        url = reverse('task-snooze', args=[self.task.pk])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        
        self.task.refresh_from_db()
        # Snooze sets snoozed_until to today + 7 days
        expected_snooze_date = timezone.now().date() + datetime.timedelta(days=7)
        self.assertEqual(self.task.snoozed_until, expected_snooze_date)
        self.assertEqual(self.task.snooze_count, 1)
        
        # Ensure it didn't update last_performed or next_due_date
        self.assertIsNone(self.task.last_performed)

    def test_task_snooze_updates_if_no_due_date(self):
        self.task.next_due_date = None
        self.task.save()
        
        url = reverse('task-snooze', args=[self.task.pk])
        self.client.post(url)
        
        self.task.refresh_from_db()
        # Should still be today + 7 days
        expected_snooze_date = timezone.now().date() + datetime.timedelta(days=7)
        self.assertEqual(self.task.snoozed_until, expected_snooze_date)
