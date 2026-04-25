from django.db import transaction
from django.db.models import F, Count

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from stores.models import Inventory, Store
from .tasks import send_order_confirmation


class CreateOrderView(APIView):
    def post(self, request):
        store_id = request.data.get("store_id")
        items = request.data.get("items", [])

        # 🔹 Validate input
        if not store_id or not isinstance(items, list) or len(items) == 0:
            return Response(
                {"error": "Valid store_id and non-empty items list required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response(
                {"error": "Store not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Normalize & validate items
        normalized_items = {}
        for item in items:
            try:
                product_id = int(item["product_id"])
                qty = int(item["quantity_requested"])
            except (KeyError, ValueError, TypeError):
                return Response(
                    {"error": "Invalid item format"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if qty <= 0:
                return Response(
                    {"error": "Quantity must be greater than 0"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            normalized_items[product_id] = normalized_items.get(product_id, 0) + qty

        product_ids = list(normalized_items.keys())

        with transaction.atomic():
            order = Order.objects.create(store=store, status="PENDING")

            inventories = (
                Inventory.objects
                .select_for_update()
                .filter(store=store, product_id__in=product_ids)
            )

            inventory_map = {inv.product_id: inv for inv in inventories}
            rejected = False
            order_items = []

            for product_id, qty in normalized_items.items():
                inventory = inventory_map.get(product_id)

                if not inventory or inventory.quantity < qty:
                    rejected = True

                order_items.append(
                    OrderItem(
                        order=order,
                        product_id=product_id,
                        quantity_requested=qty
                    )
                )

            OrderItem.objects.bulk_create(order_items)

            if rejected:
                order.status = "REJECTED"
                order.save()

                return Response(
                    {
                        "order_id": order.id,
                        "status": "REJECTED",
                        "message": "Insufficient stock for one or more items"
                    },
                    status=status.HTTP_200_OK
                )

            # 🔹 Deduct stock
            for product_id, qty in normalized_items.items():
                Inventory.objects.filter(
                    store=store,
                    product_id=product_id
                ).update(quantity=F("quantity") - qty)

            order.status = "CONFIRMED"
            order.save()

            # 🔹 Run Celery AFTER commit
            transaction.on_commit(
                lambda: send_order_confirmation.delay(order.id)
            )

        return Response(
            {
                "order_id": order.id,
                "status": "CONFIRMED",
                "items_count": len(normalized_items),
                "message": "Order placed successfully"
            },
            status=status.HTTP_201_CREATED
        )


class StoreOrderListView(APIView):
    def get(self, request, store_id):
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response(
                {"error": "Store not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        orders = (
            Order.objects
            .filter(store=store)
            .annotate(total_items=Count('orderitem'))
            .order_by('-created_at')
        )

        data = [
            {
                "order_id": order.id,
                "status": order.status,
                "created_at": order.created_at,
                "total_items": order.total_items
            }
            for order in orders
        ]

        return Response(data, status=status.HTTP_200_OK)