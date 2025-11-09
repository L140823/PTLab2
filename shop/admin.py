from django.contrib import admin

# Register your models here.
from .models import Product, Purchase, Cart, CartItem, Order, OrderItem

admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)