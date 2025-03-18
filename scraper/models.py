import re
from decimal import Decimal
from django.db import models

class ScrapedData(models.Model):
    user_identifier = models.CharField(max_length=255, help_text="Unique identifier for the user")
    url = models.URLField()
    product_name = models.CharField(max_length=255)
    current_price = models.CharField(max_length=50)
    price_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # New field
    previous_price = models.CharField(max_length=50, null=True, blank=True)
    discount = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    update_frequency = models.IntegerField(default=6, help_text="Update interval in hours")

    def save(self, *args, **kwargs):
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
