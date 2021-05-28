from django.urls import path

from .views import (CheckoutView, HomeView, OrderSummaryView, add_to_cart,
                    product_detail, remove_from_cart,
                    remove_single_item_from_cart,PaymentView,add_coupon,RequestRefundView)
                    

app_name='core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', product_detail, name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment-view'),
    path('add-oupon/', add_coupon, name='add-coupon'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund')
    



]

