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
    name = models.CharField(max_length=255)
    location = models.ForeignKey(
        Location, null=True, on_delete=models.SET_NULL, related_name="items"
    )
    sub_location = models.CharField(max_length=30, blank=True, null=True)
    purchase_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(datetime.datetime.now().year + 1),
        ],
    )
    initial_value = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Items"

    def __str__(self):
        return self.name


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
