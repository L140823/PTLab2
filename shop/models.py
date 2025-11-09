from django.db import models


# Старые модели (пока оставляем)
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)


# НОВЫЕ модели для корзины и скидок
class Cart(models.Model):
    """Корзина для хранения товаров перед покупкой"""
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    """Товары в корзине"""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Order(models.Model):
    """Заказ с учетом скидок"""
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    total_price = models.PositiveIntegerField(default=0)
    discount_applied = models.BooleanField(default=False)


class OrderItem(models.Model):
    """Товары в заказе с учетом скидок"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField()  # цена на момент покупки
    discount = models.PositiveIntegerField(default=0)  # скидка в процентах