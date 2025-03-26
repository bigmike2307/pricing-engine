import re
from decimal import Decimal
from django.db import models

class ScrapedData(models.Model):
    UPDATE_FREQUENCIES = [
        ("minutes", "Every Few Minutes"),
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("monthly", "Monthly"),
    ]

    user_identifier = models.CharField(max_length=255, help_text="Unique identifier for the user")
    url = models.URLField()
    product_name = models.CharField(max_length=255)
    current_price = models.CharField(max_length=50)
    price_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Extracted numeric price
    previous_price = models.CharField(max_length=50, null=True, blank=True)
    discount = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    update_frequency = models.CharField(
        max_length=10,
        choices=UPDATE_FREQUENCIES,
        default="hourly",
        help_text="How often the product should be updated"
    )

    def save(self, *args, **kwargs):
        """ Extract and save numeric price from `current_price` before saving """
        self.price_value = self.extract_price(self.current_price)
        super().save(*args, **kwargs)

    def extract_price(self, price_str):
        """Extract numeric price from a string (handles '$99.99' or '99.99 USD' formats)."""
        if not price_str:
            return None  # Avoid errors on empty price
        match = re.search(r"[\d.]+", price_str.replace(",", ""))
        return Decimal(match.group()) if match else None

    def __str__(self):
        return f"{self.product_name} - {self.user_identifier}"
