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
            driver.quit()


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
                    description="Update frequency (minutes, hourly, daily, monthly)",
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
            valid_frequencies = ["minutes", "hourly", "daily", "monthly"]
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

            # Map frequency to Celery Beat interval
            frequency_map = {
                "minutes": 5,  # Every 5 minutes
                "hourly": 60,  # Every 1 hour
                "daily": 1440,  # Every 24 hours
                "monthly": 43200,  # Every 30 days
            }
            schedule_product_update(scraped_entry.id, frequency_map[update_frequency]) # Default to 60 minutes if invalid

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
