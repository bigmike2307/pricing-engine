# scraper/views.py
import logging
from rest_framework import status, generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from scraper.models import ScrapedData
from scraper.serializers import ScrapedDataSerializer, ScrapedDataSerializerUpdate
from scrapy_scraper.spiders.price_checker import setup_driver, extract_product_data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ScrapeProductView(APIView):
    @swagger_auto_schema(
        operation_summary="Scrape a product",
        operation_description="Scrape product details from a given URL and optionally save the data.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="Unique user ID"),
                "url": openapi.Schema(type=openapi.TYPE_STRING, description="Product URL to scrape"),
                "save": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Save the scraped data or not"),
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
        url = request.data.get('url')
        user_identifier = request.data.get('user_identifier')
        save_data = request.data.get('save', False)

        if not url or not user_identifier:
            return Response(
                {"error": "user_identifier and url are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        driver = setup_driver()
        try:
            product_data = extract_product_data(url, driver)
            if not product_data.get('product_name', None) or not product_data.get('current_price', None):
                logger.warning(f"Incomplete scraped data: {product_data}")
                return Response(
                    {"error": "Incomplete data.", "scraped_data": product_data},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response_data = {
                "message": "Scraping successful.",
                "scraped_data": product_data,
            }

            if save_data:
                scraped_entry = ScrapedData.objects.create(
                    user_identifier=user_identifier,
                    url=url,
                    product_name=product_data['product_name'],
                    current_price=product_data['current_price'],
                    previous_price=product_data.get('previous_price'),
                    discount=product_data.get('discount'),
                    description=product_data.get('description'),
                )
                response_data["saved_entry"] = ScrapedDataSerializer(scraped_entry).data

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return Response(
                {"error": "Failed to scrape product.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            driver.quit()


class UserScrapedDataView(APIView):
    """
    GET: List all scraped data for a user_identifier.
    PUT: Update a specific scraped product by user_identifier and id (excluding url and current_price).
    DELETE: Delete a specific scraped product by user_identifier and id.
    """

    @swagger_auto_schema(
        operation_description="Get all scraped data for a specific user_identifier.",
        manual_parameters=[
            openapi.Parameter(
                'user_identifier',
                openapi.IN_PATH,
                description="Unique user identifier",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        responses={200: ScrapedDataSerializer(many=True)}
    )
    def get(self, request, user_identifier):
        scraped_data = ScrapedData.objects.filter(user_identifier=user_identifier)
        serializer = ScrapedDataSerializer(scraped_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



    @swagger_auto_schema(
        operation_description="Delete a specific scraped product for a user_identifier using id.",
        manual_parameters=[
            openapi.Parameter(
                'user_identifier',
                openapi.IN_PATH,
                description="Unique user identifier",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'id',
                openapi.IN_QUERY,
                description="ID of the product to delete",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={204: 'Deleted successfully'}
    )
    def delete(self, request, user_identifier):
        product_id = request.query_params.get('id')
        if not product_id:
            return Response({'error': 'id is required in query parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            scraped_entry = ScrapedData.objects.get(user_identifier=user_identifier, id=product_id)
            scraped_entry.delete()
            return Response({'message': 'Deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except ScrapedData.DoesNotExist:
            return Response({'error': 'Scraped data not found.'}, status=status.HTTP_404_NOT_FOUND)
