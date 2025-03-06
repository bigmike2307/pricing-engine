from rest_framework import serializers
from scraper.models import ScrapedData


class ScrapedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedData
        fields = [
             'user_identifier', 'url', 'product_name',
            'current_price', 'price_value', 'previous_price',
            'discount', 'description', 'timestamp', 'id'
        ]

class ScrapedDataSerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = ScrapedData
        fields = [
              'current_price',
        ]