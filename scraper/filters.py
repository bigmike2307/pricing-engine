# scraper/filters.py
import django_filters
from scraper.models import ScrapedData


class ScrapedDataFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price_value', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price_value', lookup_expr='lte')
    start_date = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = ScrapedData
        fields = ['user_identifier', 'min_price', 'max_price', 'start_date', 'end_date']
