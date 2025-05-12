import re
from decimal import Decimal
from django.db import models



class Tenant(models.Model):
    user_identifier = models.CharField(max_length=255, unique=True)  # Unique identifier for the tenant (e.g., company ID)
    email = models.EmailField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user_identifier

class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    target_margin = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Competitor(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='competitors')
    name = models.CharField(max_length=255)  # Competitor name (e.g., "Competitor A")
    url = models.URLField(unique=True, blank=True)  # URL for competitor's pricing data or to scrape
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CompetitorProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='competitor_products')
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE, related_name='competitor_products')
    product_url = models.URLField()  # URL to the competitor's product page
    product_name = models.CharField(max_length=50, blank=True)
    current_price = models.CharField(max_length=50, blank=True)
    previous_price = models.CharField(max_length=50, blank=True)
    price_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)  # When the competitor price was last updated

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
        return f"{self.competitor.name} - {self.product.name}"

class CompetitorPriceHistory(models.Model):
    competitor_product = models.ForeignKey(CompetitorProduct, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.competitor_product} - {self.price} on {self.recorded_at}"

# 7. Price Recommendation (result of the engine)
class PriceRecommendation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recommended_price = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    competitor_data_used = models.JSONField(blank=True, null=True)
    calculated_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Recommendation for {self.product.name} - {self.recommended_price}"

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
