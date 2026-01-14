from django.test import TestCase
from django.contrib.auth import get_user_model
from upkeep.models import Location, Item
import datetime

from common.models import Account, Profile

User = get_user_model()

class UpkeepModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='modeluser', password='password')
        self.account = Account.objects.create(name="Test Household", owner=self.user)
        self.profile = Profile.objects.create(user=self.user, account=self.account)

    def test_location_creation(self):
        location = Location.objects.create(
            name="Garden",
            user=self.user,
            account=self.account,
            default=True
        )
        self.assertEqual(str(location), "Garden")
        self.assertTrue(location.default)

    def test_item_creation(self):
        location = Location.objects.create(name="Garage", user=self.user, account=self.account)
        item = Item.objects.create(
            name="Lawn Mower",
            location=location,
            user=self.user,
            account=self.account,
            status=Item.ItemStatus.ACTIVE
        )
        self.assertEqual(str(item), "Lawn Mower")
        self.assertEqual(item.get_status_display_name(), "Active")
        self.assertEqual(item.get_status_badge_class(), "status-active")

    def test_item_warranty(self):
        location = Location.objects.create(name="Kitchen", user=self.user, account=self.account)
        future_date = datetime.date.today() + datetime.timedelta(days=365)
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        
        item_ok = Item.objects.create(
            name="Fridge",
            location=location,
            user=self.user,
            account=self.account,
            warranty_expiration=future_date
        )
        item_expired = Item.objects.create(
            name="Old Toaster",
            location=location,
            user=self.user,
            account=self.account,
            warranty_expiration=past_date
        )
        
        self.assertTrue(item_ok.is_under_warranty())
        self.assertFalse(item_expired.is_under_warranty())
