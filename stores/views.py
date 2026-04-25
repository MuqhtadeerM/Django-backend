from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Inventory, Store


class StoreInventoryView(APIView):
    def get(self, request, store_id):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response(
                {"error": "Store not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        inventory = (
            Inventory.objects
            .filter(store=store)
            .select_related('product', 'product__category')
            .order_by('product__title')
        )

        data = [
            {
                "product_title": item.product.title,
                "price": item.product.price,
                "category": item.product.category.name,
                "quantity": item.quantity
            }
            for item in inventory
        ]

        return Response(data, status=status.HTTP_200_OK)