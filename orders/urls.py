from django.urls import path
from .views import CreateOrderView, StoreOrderListView

urlpatterns = [
    path('orders/', CreateOrderView.as_view()),
    path('stores/<int:store_id>/orders/', StoreOrderListView.as_view()),
]