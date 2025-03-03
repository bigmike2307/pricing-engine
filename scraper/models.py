from django.db import models
import re


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

    def save(self, *args, **kwargs):
        self.price_value = self.extract_price(self.current_price)
        super().save(*args, **kwargs)

    def extract_price(self, price_str):
        match = re.search(r"[\d,.]+", price_str.replace(",", ""))
        return float(match.group()) if match else None

    def __str__(self):
        return f"{self.product_name} - {self.current_price}"
