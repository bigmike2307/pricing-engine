from rest_framework import serializers
from scraper.models import *


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


from rest_framework import serializers
from .models import Tenant, Product, Competitor, CompetitorProduct, CompetitorPriceHistory, PriceRecommendation, ScrapedData


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'user_identifier', 'email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'tenant', 'name', 'description', 'cost_price', 'target_margin', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompetitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competitor
        fields = ['id', 'tenant', 'name', 'url', 'created_at']
        read_only_fields = ['id', 'created_at']


class CompetitorProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    competitor = CompetitorSerializer(read_only=True)

    class Meta:
        model = CompetitorProduct
        fields = ['id', 'product', 'competitor', 'product_url', 'current_price', 'previous_price', 'price_value', 'last_checked']
        read_only_fields = ['id', 'last_checked']


class CompetitorPriceHistorySerializer(serializers.ModelSerializer):
    competitor_product = CompetitorProductSerializer(read_only=True)

    class Meta:
        model = CompetitorPriceHistory
        fields = ['id', 'competitor_product', 'price', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']

class CompetitorProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitorProduct
        fields = '__all__'

class PriceRecommendationSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = PriceRecommendation
        fields = ['id', 'product', 'recommended_price', 'reason', 'competitor_data_used', 'calculated_at']
        read_only_fields = ['id', 'calculated_at']


class ScrapedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedData
        fields = ['id', 'user_identifier', 'url', 'product_name', 'current_price', 'price_value', 'previous_price', 'discount', 'is_active', 'description', 'timestamp', 'update_frequency']
        read_only_fields = ['id', 'timestamp']
