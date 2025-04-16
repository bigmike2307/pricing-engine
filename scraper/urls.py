from django.urls import path
from .views import  *

urlpatterns = [
    path('scrape-product/', PreviewScrapeProductView.as_view(), name='scrape-product'),
    path('save-and-automate/', SaveAndAutomateProductView.as_view(), name='save-and-automate-product'),
    path('products/', ListSavedProductsView.as_view(), name='list-saved-products'),
    path('products/<int:product_id>/', RetrieveScrapedProductView.as_view(), name='retrieve-scraped-product'),
    path('products/<int:product_id>/delete/', DeleteScrapedProductView.as_view(), name='delete-scraped-product'),
    path('products/<int:product_id>/update-settings/', UpdateScrapeSettingsView.as_view(),
         name='update-scrape-settings'),

]
