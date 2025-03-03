from django.urls import path
from .views import  *

urlpatterns = [
    path('scrape-product/', ScrapeProductView.as_view(), name='scrape-product'),
    path('scraped-data/<str:user_identifier>/', UserScrapedDataView.as_view(), name='user-scraped-data'),
]
