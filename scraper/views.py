from celery.result import AsyncResult
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from scraper.models import ScrapedData
from scraper.serializers import ScrapedDataSerializer

import logging

from scraper.task import schedule_product_update, update_scraped_data
from scrapy_scraper.spiders.price_checker import setup_driver, extract_product_data

logger = logging.getLogger(__name__)

class PreviewScrapeProductView(APIView):
    """
    Scrapes product details and returns a preview. Requires `user_identifier` and `url`.
    """

    @swagger_auto_schema(
        operation_summary="Preview a product scrape",
        operation_description="Scrape product details from a given URL without saving them.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="Unique user ID"),
                "url": openapi.Schema(type=openapi.TYPE_STRING, description="Product URL to scrape"),
            },
            required=["user_identifier", "url"],
        ),
        responses={
            200: openapi.Response("Scraping successful"),
            400: openapi.Response("Invalid request"),
            500: openapi.Response("Scraping failed"),
        },
    )
    def post(self, request):
        user_identifier = request.data.get('user_identifier')
        url = request.data.get('url')

        if not user_identifier or not url:
            return Response(
                {"error": "user_identifier and url are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        driver = setup_driver()
        try:
            product_data = extract_product_data(url, driver)

            if not product_data.get('product_name') or not product_data.get('current_price'):
                logger.warning(f"Incomplete scraped data: {product_data}")
                return Response(
                    {"error": "Incomplete data.", "scraped_data": product_data},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {
                    "message": "Scraping successful.",
                    "user_identifier": user_identifier,
                    "scraped_data": product_data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return Response(
                {"error": "Failed to scrape product.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        finally:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Driver quit failed: {e}")


class SaveAndAutomateProductView(APIView):
    """ Saves the scraped data and starts a background task for updates. """

    @swagger_auto_schema(
        operation_summary="Save and Automate product updates",
        operation_description="Scrape, save, and automate product monitoring.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="Unique user ID"),
                "url": openapi.Schema(type=openapi.TYPE_STRING, description="Product URL"),
                "update_frequency": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Update frequency (minutes, hourly, daily, weekly, monthly)",
                    default="hourly"
                ),
            },
            required=["user_identifier", "url"],
        ),
        responses={
            200: openapi.Response("Scraping successful, automation started."),
            400: openapi.Response("Invalid request or incomplete data."),
            500: openapi.Response("Scraping failed."),
        },
    )
    def post(self, request):
        try:
            # Extract required data
            user_identifier = request.data.get('user_identifier')
            url = request.data.get('url')
            update_frequency = str(request.data.get('update_frequency', "hourly")).lower()  # Ensure it's a string

            if not user_identifier or not url:
                return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

            # Validate update frequency
            valid_frequencies = ["minutes", "hourly", "daily", "weekly", "monthly"]
            if update_frequency not in valid_frequencies:
                return Response(
                    {"error": f"Invalid update frequency. Choose from {valid_frequencies}."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🚀 **Scrape product data immediately**
            driver = setup_driver()
            try:
                product_data = extract_product_data(url, driver)
                if not product_data.get("product_name") or not product_data.get("current_price"):
                    logger.warning(f"Incomplete scraped data: {product_data}")
                    return Response(
                        {"error": "Incomplete data.", "scraped_data": product_data},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")
                return Response(
                    {"error": "Failed to scrape product.", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            finally:
                driver.quit()

            # Save the scraped product
            scraped_entry = ScrapedData.objects.create(
                user_identifier=user_identifier,
                url=url,
                product_name=product_data["product_name"],
                current_price=product_data["current_price"],
                previous_price=product_data.get("previous_price"),
                discount=product_data.get("discount"),
                description=product_data.get("description"),
                update_frequency=str(update_frequency),   # Ensure only valid string values are stored
            )


            schedule_product_update(scraped_entry.id, update_frequency) # Default to 60 minutes if invalid

              # Pass integer here, not save it to model

            return Response(
                {
                    "message": "Scraping successful. Product saved and automation started.",
                    "user_identifier": user_identifier,
                    "scraped_data": product_data,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from scraper.models import ScrapedData
from scraper.serializers import ScrapedDataSerializer
import logging
from scraper.task import schedule_product_update, update_scraped_data

logger = logging.getLogger(__name__)

class ListSavedProductsView(APIView):
    """
    List all saved products for a given user.
    """
    @swagger_auto_schema(
        operation_summary="List all saved products",
        operation_description="Retrieve all products a user has saved.",
        manual_parameters=[
            openapi.Parameter('user_identifier', openapi.IN_QUERY, description="Unique user ID", type=openapi.TYPE_STRING, required=True)
        ],
        responses={200: ScrapedDataSerializer(many=True)}
    )
    def get(self, request):
        user_identifier = request.query_params.get('user_identifier')
        if not user_identifier:
            return Response({"error": "user_identifier is required."}, status=status.HTTP_400_BAD_REQUEST)
        products = ScrapedData.objects.filter(user_identifier=user_identifier)
        serializer = ScrapedDataSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RetrieveScrapedProductView(APIView):
    """
    Retrieve a specific product by ID for a given user.
    """
    @swagger_auto_schema(
        operation_summary="Retrieve a specific scraped product",
        operation_description="Get details of a single scraped product by ID.",
        manual_parameters=[
            openapi.Parameter('user_identifier', openapi.IN_QUERY, description="Unique user ID", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('product_id', openapi.IN_PATH, description="Product ID", type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: ScrapedDataSerializer()}
    )
    def get(self, request, product_id):
        user_identifier = request.query_params.get('user_identifier')
        if not user_identifier:
            return Response({"error": "user_identifier is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = ScrapedData.objects.get(id=product_id, user_identifier=user_identifier)
            return Response(ScrapedDataSerializer(product).data, status=status.HTTP_200_OK)
        except ScrapedData.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

class DeleteScrapedProductView(APIView):
    """
    Delete a saved product for a given user.
    """
    @swagger_auto_schema(
        operation_summary="Delete a scraped product",
        operation_description="Remove a saved product.",
        manual_parameters=[
            openapi.Parameter('user_identifier', openapi.IN_QUERY, description="Unique user ID", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('product_id', openapi.IN_PATH, description="Product ID", type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={204: "Product deleted successfully."}
    )
    def delete(self, request, product_id):
        user_identifier = request.query_params.get('user_identifier')
        if not user_identifier:
            return Response({"error": "user_identifier is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = ScrapedData.objects.get(id=product_id, user_identifier=user_identifier)
            product.delete()
            return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ScrapedData.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

class UpdateScrapeSettingsView(APIView):
    """
    Update scrape settings (update frequency) for a saved product.
    """
    @swagger_auto_schema(
        operation_summary="Update scrape settings",
        operation_description="Modify update frequency for an existing product.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="Unique user ID"),
                "update_frequency": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Update frequency (minutes, hourly, daily, weekly, monthly)",
                    default="hourly"
                )
            },
            required=["user_identifier", "update_frequency"]
        ),
        responses={200: "Update successful."}
    )
    def patch(self, request, product_id):
        user_identifier = request.data.get('user_identifier')
        update_frequency = request.data.get('update_frequency')
        if not user_identifier or not update_frequency:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = ScrapedData.objects.get(id=product_id, user_identifier=user_identifier)
            product.update_frequency = update_frequency
            product.save()
            schedule_product_update(product.id, update_frequency)
            return Response({"message": "Update frequency updated successfully."}, status=status.HTTP_200_OK)
        except ScrapedData.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)



