import datetime
from django.db import models
from common.models import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator


class Location(BaseModel):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    country_code = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Locations"

    def __str__(self):
        return self.name


class Item(BaseModel):
    class ItemStatus(models.IntegerChoices):
        ACTIVE = 1, "Active"
        RETIRED = 2, "Retired"
        BROKEN = 3, "Broken"

    # Mandatory
    name = models.CharField(max_length=255)
    location = models.ForeignKey(
        Location, null=True, on_delete=models.SET_NULL, related_name="items"
    )
    status = models.IntegerField(
        choices=ItemStatus, null=False, default=ItemStatus.ACTIVE
    )
    quantity = models.PositiveIntegerField(default=1)

    # Optional metadata
    area = models.CharField(max_length=30, blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    model_number = models.CharField(max_length=255, blank=True, null=True)
    serial_number = models.CharField(max_length=255, blank=True, null=True)

    purchase_value = models.PositiveIntegerField(null=True, blank=True)
    purchase_place = models.CharField(max_length=255, blank=True, null=True)
    purchase_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(datetime.datetime.now().year + 1),
        ],
    )
    warranty_expiration = models.DateField(blank=True, null=True)
    receipt_file = models.FileField(upload_to="receipts/", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    manufacturer_manual_url = models.URLField(null=True, blank=True)

    end_of_service_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Items"

    def __str__(self):
        return self.name

    def is_under_warranty(self):
        return self.warranty_expiration and self.warranty_expiration >= datetime.date()

    def get_status_badge_class(self):
        return {
            self.ItemStatus.ACTIVE: "status-active",
            self.ItemStatus.RETIRED: "status-retired",
            self.ItemStatus.BROKEN: "status-broken",
        }.get(self.status, "status-active")

    def get_status_display_name(self):
        return self.ItemStatus(self.status).label


class Task(BaseModel):
    class Frequency(models.IntegerChoices):
        DAILY = 1, "Daily"
        WEEKLY = 7, "Weekly"
        BI_WEEKLY = 14, "Bi-weekly"
        MONTHLY = 30, "Monthly"
        BI_MONTHLY = 60, "Bi-monthly"
        QUARTERLY = 90, "Quarterly"
        YEARLY = 365, "Yearly"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    description_url = models.URLField(blank=True, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="tasks")
    frequency = models.IntegerField(choices=Frequency.choices, null=False)
    estimated_hours_to_complete = models.PositiveIntegerField(blank=True, null=True)
    last_performed = models.DateField(blank=True, null=True)
    next_due_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Tasks"

    def __str__(self):
        return f"{self.name} ({self.item.name})"

    def calculate_next_due_date(self):
        if self.last_performed and self.frequency:
            return self.last_performed + datetime.timedelta(days=self.frequency)
        if not self.last_performed:
            return datetime.date.today()

    def save(self, *args, **kwargs):
        self.next_due_date = self.calculate_next_due_date()
        super().save(*args, **kwargs)
