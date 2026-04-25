from django.db import models

# Create your models here.
from django.db import models
from products.models import Product

class Store(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

class Inventory(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('store', 'product')