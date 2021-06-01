from django.contrib import admin
from django import forms
from django.forms.utils import ErrorList
from .models import Item, OrderItem, Order, Banner, BillingAddress, Coupon, Refund, ShippingAddress,Payment,UserProfile

def make_refund_accepted(modeladmin,request,queryset):
    for order in queryset:
        if order.request_refund==True:
            queryset.update(accepted_refund=True)
        else:
            raise forms.ValidationError("There is no refund request received yet")
        
        
    
    
make_refund_accepted.short_description='Update selected orders for refund accepted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user','ordered','being_delivered','received','request_refund','accepted_refund','billing_address','shipping_address','payment','coupon']
    list_filter = ['ordered','being_delivered','received','request_refund','accepted_refund']
    list_display_links = ['user','billing_address','shipping_address','payment','coupon']
    search_fields = ['user__username','reference_code']
    actions = [make_refund_accepted]
    
    
    
    



admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order,OrderAdmin)
admin.site.register(Banner)
admin.site.register(BillingAddress)
admin.site.register(ShippingAddress)
admin.site.register(Coupon)
admin.site.register(Payment)
admin.site.register(Refund)
admin.site.register(UserProfile)





