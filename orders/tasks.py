# orders/tasks.py
from celery import shared_task

@shared_task
def send_order_confirmation(order_id):
    print(f"Order {order_id} confirmed!")