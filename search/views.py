from django.shortcuts import render

# Create your views here.
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from products.models import Product
from stores.models import Inventory
from django.core.cache import cache


from django.core.cache import cache

class ProductSearchView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        category = request.GET.get("category")
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")
        store_id = request.GET.get("store_id")
        in_stock = request.GET.get("in_stock")
        sort = request.GET.get("sort")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))

        # 🔹 Build cache key (VERY IMPORTANT)
        cache_key = f"""
        search:{query}:{category}:{min_price}:{max_price}:
        {store_id}:{in_stock}:{sort}:{page}:{limit}
        """

        # 🔹 Check cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 🔹 If not cached → run DB query
        products = Product.objects.all()

        if query:
            products = products.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )

        if category:
            products = products.filter(category__name__icontains=category)

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        if store_id:
            products = products.filter(inventory__store_id=store_id)

        if in_stock == "true":
            products = products.filter(inventory__quantity__gt=0)

        products = products.distinct()

        if sort == "price":
            products = products.order_by("price")
        elif sort == "-price":
            products = products.order_by("-price")
        elif sort == "newest":
            products = products.order_by("-id")

        start = (page - 1) * limit
        end = start + limit

        total = products.count()
        products = products[start:end]

        data = []

        for product in products:
            item = {
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "category": product.category.name,
            }

            if store_id:
                inventory = Inventory.objects.filter(
                    product=product,
                    store_id=store_id
                ).first()

                item["quantity"] = inventory.quantity if inventory else 0

            data.append(item)

        response_data = {
            "total": total,
            "page": page,
            "limit": limit,
            "results": data
        }

        # 🔹 Store in cache (5 minutes)
        cache.set(cache_key, response_data, timeout=300)

        return Response(response_data)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Case, When, IntegerField
from django.core.cache import cache
from products.models import Product


class ProductSuggestView(APIView):
    def get(self, request):
        query = request.GET.get("q", "").strip()

        # 🔹 Minimum 3 characters required
        if len(query) < 3:
            return Response(
                {"error": "Minimum 3 characters required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Cache key
        cache_key = f"search:{query}:{category}:{min_price}:{max_price}:{store_id}:{in_stock}:{sort}:{page}:{limit}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # 🔹 Prefix priority (IMPORTANT requirement)
        suggestions = (
            Product.objects
            .filter(title__icontains=query)
            .annotate(
                priority=Case(
                    When(title__istartswith=query, then=0),  # prefix match first
                    default=1,
                    output_field=IntegerField()
                )
            )
            .order_by("priority", "title")
            .values_list("title", flat=True)
            .distinct()[:10]
        )

        result = list(suggestions)

        # 🔹 Cache for fast response
        cache.set(cache_key, result, timeout=300)

        return Response(result, status=status.HTTP_200_OK)