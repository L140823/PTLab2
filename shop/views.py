from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic.edit import CreateView
from .models import Product, Purchase, Cart, CartItem, Order, OrderItem
import uuid


def _get_or_create_cart(request):
    """Получить или создать корзину для сессии"""
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            return Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            pass

    # Создаем новую корзину
    cart = Cart.objects.create(session_key=str(uuid.uuid4()))
    request.session['cart_id'] = cart.id
    return cart


def _calculate_discount(cart_items):
    """Рассчитать скидку 40% на третий товар при покупке двух разных товаров"""
    if len(cart_items) < 3:
        return None, 0

    # Получаем уникальные товары среди первых двух
    first_two_products = set()
    for i in range(min(2, len(cart_items))):
        first_two_products.add(cart_items[i].product)

    # Условие для скидки: первые два товара разные
    if len(first_two_products) >= 2:
        # Скидка применяется к третьему товару
        discount_product = cart_items[2].product
        discount_amount = discount_product.price * 0.4  # 40% скидка
        return discount_product, discount_amount

    return None, 0


def product_list(request):
    """Главная страница товаров с корзиной"""
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})


def add_to_cart(request, product_id):
    """Добавить товар в корзину (линейно, без суммирования)"""
    if request.method == 'POST':
        cart = _get_or_create_cart(request)
        product = get_object_or_404(Product, id=product_id)

        # Добавляем товар как отдельную строку (не суммируем)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1  # всегда 1, так как добавляем линейно
        )

        # Возвращаем на ту же страницу вместо редиректа в корзину
        return redirect('product_list')
    return redirect('product_list')


def cart_view(request):
    """Просмотр корзины"""
    cart = _get_or_create_cart(request)
    cart_items = CartItem.objects.filter(cart=cart).order_by('id')  # Сортируем по порядку добавления

    # Считаем сумму для каждого товара
    items_with_total = []
    total = 0
    discount_product, discount_amount = _calculate_discount(cart_items)

    for index, item in enumerate(cart_items):
        item_price = item.product.price
        item_discount = 0

        # Применяем скидку к третьему товару
        if discount_product and item.product == discount_product and index == 2:
            item_discount = discount_amount
            item_price_with_discount = item_price - item_discount
        else:
            item_price_with_discount = item_price

        item_total = item_price_with_discount
        items_with_total.append({
            'item': item,
            'index': index + 1,  # номер по порядку
            'total': item_total,
            'discount': item_discount,
            'has_discount': item_discount > 0
        })
        total += item_total

    context = {
        'items_with_total': items_with_total,
        'total': total,
        'discount_applied': discount_amount > 0,
        'discount_amount': discount_amount
    }
    return render(request, 'shop/cart.html', context)


def remove_from_cart(request, item_id):
    """Удалить товар из корзины"""
    if request.method == 'POST':
        try:
            cart_item = CartItem.objects.get(id=item_id)
            cart_item.delete()
        except CartItem.DoesNotExist:
            pass
    return redirect('cart_view')


class PurchaseCreate(CreateView):
    """Форма покупки"""
    model = Purchase
    fields = ['person', 'address']
    template_name = 'shop/purchase_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Убираем поле product из формы, так как берем из корзины
        if 'product' in form.fields:
            del form.fields['product']
        return form

    def form_valid(self, form):
        # Сохраняем покупку для каждого товара в корзине
        cart_id = self.request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
                cart_items = CartItem.objects.filter(cart=cart).order_by('id')

                # Рассчитываем скидку
                discount_product, discount_amount = _calculate_discount(cart_items)

                # Создаем покупку для каждого товара
                for index, item in enumerate(cart_items):
                    purchase = Purchase(
                        product=item.product,
                        person=form.cleaned_data['person'],
                        address=form.cleaned_data['address']
                    )
                    purchase.save()

                # Очищаем корзину
                cart_items.delete()
                del self.request.session['cart_id']

            except Cart.DoesNotExist:
                pass

        return HttpResponse(f'Спасибо за покупку, {form.cleaned_data["person"]}!')