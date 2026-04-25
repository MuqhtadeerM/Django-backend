from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Store, Inventory

admin.site.register(Store)
admin.site.register(Inventory)