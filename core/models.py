from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField

from django.db.models.signals import post_save

# Create your models here.
CATEGORY_CHOICES=(
    ('Shirts','Shirts'),
    ('iPhone','iPhone'),
    ('Samsung','Samsung'),
    ('Haier','Haier'),
    
)

LABEL_CHOICES=(
    ('P','primary'),
    ('S','secondary'),
    ('D','danger'),
)
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Item(models.Model):
    item_name = models.CharField(max_length=100)
    item_price = models.FloatField()
    discount_price = models.FloatField(blank=True,null=True)
    category = models.CharField(choices=CATEGORY_CHOICES,max_length=20)
    label = models.CharField(choices=LABEL_CHOICES, max_length=20)
    image = models.ImageField(upload_to="product",blank=True,null=True)
    slug = models.SlugField(unique=True, blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    item_spltag = models.CharField(blank=True,null=True,max_length=20)
    additional_info = models.TextField(blank=True,null=True)


    def __str__(self):
        return self.item_name
    
    def get_add_to_cart_url(self):
        return reverse('core:add-to-cart',kwargs={
            'slug':self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('core:remove-from-cart',kwargs={
            'slug':self.slug
        })
        
class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,blank=True,null=True)
    ordered = models.BooleanField(default=False,blank=True,null=True)
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    item_qty = models.IntegerField(default=1)

    def __str__(self):
        return f"{ self.item_qty } of { self.item.item_name}"
    
    def get_total_item_price(self):
        return self.item_qty * self.item.item_price
    
    def get_total_discount_item_price(self):
        return self.item_qty * self.item.discount_price
    
    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        else:
            return self.get_total_item_price()


class Order(models.Model):
    reference_code = models.CharField(max_length=20)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_items = models.ManyToManyField(OrderItem)
    ordered = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    billing_address = models.ForeignKey('BillingAddress',on_delete=models.SET_NULL,blank=True,null=True)
    shipping_address = models.ForeignKey('ShippingAddress',on_delete=models.SET_NULL,blank=True,null=True) 
    payment = models.ForeignKey('Payment',on_delete=models.SET_NULL,blank=True,null=True)
    coupon = models.ForeignKey('Coupon',on_delete=models.SET_NULL,blank=True,null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    request_refund = models.BooleanField(default=False)
    accepted_refund = models.BooleanField(default=False)
    
    
    
    ''' 
    1. product added to cart
    2. adding billing address (failed checkout)
    3. then we select the payment option
    4. product deliver procedure (packaging, handover to courier company) - being deliver
    5. Finally delivered (received)
    6. in case any refunds
    '''

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.order_items.all():
            total+=order_item.get_final_price()
        if self.coupon:
            total-=self.coupon.amount
        return total

    def get_total_save(self):
        total_save = 0
        for order_item in self.order_items.all():
            total_save+=order_item.get_amount_saved()
        return total_save
    
class Banner(models.Model):
    b_image = models.ImageField(upload_to="banner")
    b_title = models.CharField(max_length=30)
    b_description1  = models.TextField(max_length=30)
    b_description2  = models.TextField(max_length=30)
    
    
    def __str__(self):
        return self.b_title

class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    appt_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=30)
    default = models.BooleanField(default=False)

    # TODO:add functionality of the bills
    # same_billing_address = models.CharField(max_length=30)
    # save_info = models.CharField(max_length=30)
    # payment_option = models.CharField(max_length=30)
    # payment_option = forms.ChoiceField(widget=forms.RadioSelect,choices=PAYMENT_CHOICES)
    # add direct link into admin pannel

    def __str__(self):
        return self.street_address
    
class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    appt_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=30)
    phone = models.CharField(max_length=15,blank=True,null=True)
    email = models.EmailField(blank=True,null=True)
    delivery_instructions = models.CharField(max_length=100,blank=True,null=True)
    default = models.BooleanField(default=False)
    

    def __str__(self):
        return self.user.username
   
    
    

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.FloatField()
    time_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return self.code
    
class Refund(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    message = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()
    
    def __str__(self):
        return f"{self.pk}" 
    
    
def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)