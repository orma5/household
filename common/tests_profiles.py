from django.test import TestCase
from django.contrib.auth import get_user_model
from common.models import Profile

User = get_user_model()

class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='password')

    def test_profile_str(self):
        profile = Profile.objects.create(user=self.user, full_name="John Doe")
        self.assertEqual(str(profile), "Profile for profileuser")
        self.assertEqual(profile.full_name, "John Doe")

    def test_profile_auto_creation_logic_in_views(self):
        # We check if the settings view correctly handles profile creation
        # (Based on the logic in upkeep/views.py where it does get_or_create)
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        client.login(username='profileuser', password='password')
        
        # Accessing settings should ensure profile exists
        # But first delete it if it was created in setUp or manually
        Profile.objects.all().delete()
        
        response = client.get(reverse('settings-view'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
