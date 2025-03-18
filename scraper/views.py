from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from scraper.models import ScrapedData
from scraper.serializers import ScrapedDataSerializer

import logging

from scraper.task import schedule_product_update
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
    """
    Saves the scraped data and starts background task for updates.
    """

    @swagger_auto_schema(
        operation_summary="Save and Automate product updates",
        operation_description="Save the scraped product details and begin background monitoring.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="Unique user ID"),
                "url": openapi.Schema(type=openapi.TYPE_STRING, description="Product URL"),
                "product_name": openapi.Schema(type=openapi.TYPE_STRING, description="Product name"),
                "current_price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Current price"),
                "previous_price": openapi.Schema(type=openapi.TYPE_NUMBER, description="Previous price (optional)"),
                "discount": openapi.Schema(type=openapi.TYPE_STRING, description="Discount (optional)"),
                "description": openapi.Schema(type=openapi.TYPE_STRING, description="Product description (optional)"),
                "update_frequency": openapi.Schema(type=openapi.TYPE_INTEGER, description="Update interval in hours", default=6),
            },
            required=["user_identifier", "url", "product_name", "current_price"],
        ),
        responses={
            200: openapi.Response("Saved successfully, automation started."),
            400: openapi.Response("Invalid request"),
        },
    )
    def post(self, request):
        user_identifier = request.data.get('user_identifier')
        url = request.data.get('url')
        product_name = request.data.get('product_name')
        current_price = request.data.get('current_price')
        previous_price = request.data.get('previous_price')
        discount = request.data.get('discount')
        description = request.data.get('description')
        update_frequency = request.data.get('update_frequency', 6)

        if not user_identifier or not url or not product_name or not current_price:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save the scraped product
        scraped_entry = ScrapedData.objects.create(
            user_identifier=user_identifier,
            url=url,
            product_name=product_name,
            current_price=current_price,
            previous_price=previous_price,
            discount=discount,
            description=description,
            update_frequency=update_frequency,
        )

        # Start the background task
        schedule_product_update(scraped_entry.id, update_frequency)

        return Response(
            {
                "message": "Product saved and automation started.",
                "saved_entry": ScrapedDataSerializer(scraped_entry).data
            },
            status=status.HTTP_200_OK
        )
