from scrapy_scraper.spiders.price_checker import setup_driver, extract_product_data
from .serializers import PriceRecommendationSerializer, ScrapedDataSerializer, CompetitorSerializer, ProductSerializer, \
    TenantSerializer, CompetitorProductSerializer
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from .models import Tenant, Product, Competitor, ScrapedData, PriceRecommendation, CompetitorProduct
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .utils import recommend_optimal_price


# Company Views
class CompanyListCreate(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="List all companies or create a new company")
    def get(self, request):
        companies = Tenant.objects.all()
        serializer = TenantSerializer(companies, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new company",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="User_identifier"),
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Company email address"),
            },
            required=["user_identifier",  "email"],
        ),
        responses={
            201: openapi.Response("Company created successfully."),
            400: openapi.Response("Invalid data provided."),
        },
    )
    def post(self, request):
        """
        Creates a new company and returns the created company data.
        """
        serializer = TenantSerializer(data=request.data)

        if serializer.is_valid():
            # Save the new company to the database
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # If the provided data is invalid, return a 400 error with validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetail(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Retrieve a company by ID")
    def get(self, request, id):
        try:
            company = Tenant.objects.get(id=id)
        except Tenant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TenantSerializer(company)
        return Response(serializer.data)

    @swagger_auto_schema(operation_description="Update a company by ID", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_identifier": openapi.Schema(type=openapi.TYPE_STRING, description="User_identifier"),
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Company email address"),
            },
            required=["user_identifier",  "email"],
        ),)
    def put(self, request, id):
        try:
            company = Tenant.objects.get(id=id)
        except Tenant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TenantSerializer(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Delete a company by ID")
    def delete(self, request, id):
        try:
            company = Tenant.objects.get(id=id)
            company.delete()
        except Tenant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Product Views
class ProductListCreate(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="List all products or create a new product", )
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
    operation_summary="Create a new product",
    operation_description="Create a new product under a specific tenant with pricing strategy.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "tenant": openapi.Schema(type=openapi.TYPE_INTEGER, description="Tenant ID"),
            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Product Name"),
            "description": openapi.Schema(type=openapi.TYPE_STRING, description="Product description"),
            "cost_price": openapi.Schema(type=openapi.TYPE_NUMBER, format="decimal", description="Cost price of the product"),
            "target_margin": openapi.Schema(type=openapi.TYPE_NUMBER, format="decimal", description="Target profit margin percentage"),
        },
        required=["tenant", "name", "description", "cost_price", "target_margin"],
    )
        )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Retrieve a product by ID")
    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    @swagger_auto_schema(operation_description="Update a product by ID")
    def put(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Delete a product by ID")
    def delete(self, request, id):
        try:
            product = Product.objects.get(id=id)
            product.delete()
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductRecommendation(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Trigger recommendation for a product",
        responses={201: PriceRecommendationSerializer()}
    )
    def post(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        cost_price = product.cost_price
        margin = product.target_margin

        # Get competitor prices for this product
        competitor_qs = CompetitorProduct.objects.filter(product=product, price_value__isnull=False)
        competitor_prices = list(competitor_qs.values_list("price_value", flat=True))

        # Apply recommendation logic
        recommended_price, reason = recommend_optimal_price(cost_price, margin, competitor_prices)

        # Save the recommendation
        recommendation = PriceRecommendation.objects.create(
            product=product,
            recommended_price=recommended_price,
            #reason=reason,
            competitor_data_used={
                "prices": [float(p) for p in competitor_prices],  # Convert Decimal to float
                "sources": [cp.competitor.name for cp in competitor_qs],
            },
        )

        return Response(PriceRecommendationSerializer(recommendation).data, status=status.HTTP_201_CREATED)

# Competitor Views
class CompetitorListCreate(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="List or add a competitor")
    def get(self, request):
        competitors = Competitor.objects.all()
        serializer = CompetitorSerializer(competitors, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
    operation_summary="Add a new competitor",
    operation_description="Create a new competitor associated with a tenant for price monitoring.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "tenant": openapi.Schema(type=openapi.TYPE_INTEGER, description="Tenant ID the competitor belongs to"),
            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name of the competitor (e.g., 'Amazon')"),
            "url": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="Unique URL to scrape or pull pricing data from"),
        },
        required=["tenant", "name", "url"]
    )
)
    def post(self, request):
        serializer = CompetitorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompetitorDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Retrieve/update/delete a competitor by ID")
    def get(self, request, id):
        try:
            competitor = Competitor.objects.get(id=id)
        except Competitor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CompetitorSerializer(competitor)
        return Response(serializer.data)

    def put(self, request, id):
        try:
            competitor = Competitor.objects.get(id=id)
        except Competitor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CompetitorSerializer(competitor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            competitor = Competitor.objects.get(id=id)
            competitor.delete()
        except Competitor.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)



class CompetitorProductListView(APIView):
    queryset = CompetitorProduct.objects.all()
    serializer_class = CompetitorProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="List all competitor products")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ScrapeAndCreateCompetitorProduct(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Scrape competitor product and optionally save.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["product", "competitor", "product_url"],
            properties={
                "product": openapi.Schema(type=openapi.TYPE_INTEGER),
                "competitor": openapi.Schema(type=openapi.TYPE_INTEGER),
                "product_url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
                "save": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False)
            },
        ),
        responses={201: CompetitorProductSerializer()}
    )
    def post(self, request):
        product_id = request.data.get("product")
        competitor_id = request.data.get("competitor")
        url = request.data.get("product_url")
        save = request.data.get("save", False)

        if not (product_id and competitor_id and url):
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        driver = setup_driver()
        try:
            scraped = extract_product_data(url, driver)
            if not scraped.get("product_name") or not scraped.get("current_price"):
                return Response(
                    {"error": "Incomplete data.", "scraped_data": scraped},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({"error": "Scraping failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            driver.quit()

        data = {
            "product": product_id,
            "competitor": competitor_id,
            "product_url": url,
            "current_price": scraped.get("current_price"),
            "previous_price": scraped.get("previous_price", ""),
        }

        serializer = CompetitorProductSerializer(data=data)
        if serializer.is_valid():
            if save:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"scraped_data": serializer.data, "message": "Not saved. Use save=true to persist."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompetitorProductDetailView(APIView):
    #permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return CompetitorProduct.objects.get(pk=pk)
        except CompetitorProduct.DoesNotExist:
            return None

    @swagger_auto_schema(operation_description="Retrieve a competitor product")
    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompetitorProductSerializer(obj)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a competitor product (full)",
        request_body=CompetitorProductSerializer
    )
    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompetitorProductSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Update a competitor product (partial)",
        request_body=CompetitorProductSerializer
    )
    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompetitorProductSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_description="Delete a competitor product")
    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ScrapedData Views
class ScrapeData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Scrape competitor data immediately")
    def post(self, request):
        # Scraping logic here (not implemented in the example)
        return Response({"status": "scrape started"}, status=status.HTTP_200_OK)


class ScrapedDataList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="View all scraped data")
    def get(self, request):
        scraped_data = ScrapedData.objects.all()
        serializer = ScrapedDataSerializer(scraped_data, many=True)
        return Response(serializer.data)


class ScrapedDataDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="View scraped data for a specific product")
    def get(self, request, product_id):
        scraped_data = ScrapedData.objects.filter(id=product_id)
        if not scraped_data.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ScrapedDataSerializer(scraped_data, many=True)
        return Response(serializer.data)


# Recommendations Views
class RecommendationList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="View all recommendations")
    def get(self, request):
        recommendations = PriceRecommendation.objects.all()
        serializer = PriceRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)


class RecommendationDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="View recommendation for a product")
    def get(self, request, product_id):
        try:
            recommendation = PriceRecommendation.objects.get(product__id=product_id)
        except PriceRecommendation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = PriceRecommendationSerializer(recommendation)
        return Response

