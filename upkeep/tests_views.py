from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from .models import Location, Item, Task

User = get_user_model()

class UpkeepViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewuser', password='password')
        self.client = Client()
        self.client.login(username='viewuser', password='password')
        
        self.location = Location.objects.create(name="Home", user=self.user, default=True)
        self.item = Item.objects.create(name="Toaster", location=self.location, user=self.user)

    def test_task_due_list_filtering(self):
        # Create one due task and one future task
        today = timezone.now().date()
        Task.objects.create(
            name="Due Task", 
            item=self.item, 
            frequency=Task.Frequency.DAILY,
            next_due_date=today
        )
        Task.objects.create(
            name="Future Task", 
            item=self.item, 
            frequency=Task.Frequency.WEEKLY,
            next_due_date=today + datetime.timedelta(days=1)
        )
        
        response = self.client.get(reverse('task-due-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Due Task")
        self.assertNotContains(response, "Future Task")

    def test_location_switching_persists(self):
        loc2 = Location.objects.create(name="Cabin", user=self.user)
        url = reverse('switch-location', args=[loc2.id])
        
        self.client.get(url)
        self.assertEqual(self.client.session['active_location_id'], loc2.id)
