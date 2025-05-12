from django.urls import path

from . import views
from .views import  *

urlpatterns = [
      # Companies endpoints
    path('companies/', views.CompanyListCreate.as_view(), name='company-list-create'),
    path('companies/<int:id>/', views.CompanyDetail.as_view(), name='company-detail'),

    # Products endpoints
    path('products/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:id>/', views.ProductDetail.as_view(), name='product-detail'),
    path('products/<int:id>/recommend/', views.ProductRecommendation.as_view(), name='product-recommendation'),

    # Competitors endpoints
    path('competitors/', views.CompetitorListCreate.as_view(), name='competitor-list-create'),
    path('competitors/<int:id>/', views.CompetitorDetail.as_view(), name='competitor-detail'),

    #   Competitors Products endpoints
    path('competitor-products/', CompetitorProductListView.as_view(), name='competitorproduct-list'),
    path('competitor-products/scrape/', ScrapeAndCreateCompetitorProduct.as_view(), name='competitorproduct-scrape'),
    path('competitor-products/<int:pk>/', CompetitorProductDetailView.as_view(), name='competitorproduct-detail'),

    # Scraped data endpoints
    path('scrape/', views.ScrapeData.as_view(), name='scrape-data'),
    path('scraped-data/', views.ScrapedDataList.as_view(), name='scraped-data-list'),
    path('scraped-data/<int:product_id>/', views.ScrapedDataDetail.as_view(), name='scraped-data-detail'),

    # Recommendations endpoints
    path('recommendations/', views.RecommendationList.as_view(), name='recommendation-list'),
    path('recommendations/<int:product_id>/', views.RecommendationDetail.as_view(), name='recommendation-detail'),

]

