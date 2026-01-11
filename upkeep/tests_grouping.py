from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Location, Item, Task

User = get_user_model()

class TaskGroupingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='groupuser', password='password')
        self.client = Client()
        self.client.login(username='groupuser', password='password')
        
        self.location = Location.objects.create(name="Home", user=self.user, default=True)
        
        self.item1 = Item.objects.create(name="Kitchen Fridge", location=self.location, user=self.user, area="Kitchen")
        self.item2 = Item.objects.create(name="Living Room AC", location=self.location, user=self.user, area="Living Room")
        self.item3 = Item.objects.create(name="Generic Item", location=self.location, user=self.user) # No area
        
        Task.objects.create(name="Clean Coils", item=self.item1, frequency=Task.Frequency.YEARLY)
        Task.objects.create(name="Change Filter", item=self.item2, frequency=Task.Frequency.QUARTERLY)
        Task.objects.create(name="Generic Task", item=self.item3, frequency=Task.Frequency.MONTHLY)

    def test_group_by_item(self):
        response = self.client.get(reverse('task-management-list'), {'group_by': 'item'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kitchen Fridge")
        self.assertContains(response, "Living Room AC")
        self.assertContains(response, "Generic Item")

    def test_group_by_area(self):
        response = self.client.get(reverse('task-management-list'), {'group_by': 'area'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kitchen")
        self.assertContains(response, "Living Room")
        self.assertContains(response, "General") # Default for empty area

    def test_group_by_frequency(self):
        response = self.client.get(reverse('task-management-list'), {'group_by': 'frequency'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yearly")
        self.assertContains(response, "Quarterly")
        self.assertContains(response, "Monthly")
