from django.urls import path
from .views import  *

urlpatterns = [
    path('scrape-product/', PreviewScrapeProductView.as_view(), name='scrape-product'),
    path('save-and-automate/', SaveAndAutomateProductView.as_view(), name='save-and-automate-product'),
]
