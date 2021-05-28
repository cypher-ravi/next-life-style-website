from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, View
from django.conf import settings
from django.http import HttpResponseRedirect

from .models import Banner, Item, Order, OrderItem, BillingAddress, Payment, Coupon, Refund, ShippingAddress
from .forms import CheckoutForm, RefundForm

import random
import string

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
# stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"

# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token


# Create your views here.

def create_reference_code():
    return ''.join(random.choice(string.ascii_lowercase+string.ascii_uppercase+string.digits,k=20))


class HomeView(ListView):
    model = Item
    paginate_by=3
    template_name = "home.html"

    def get_context_data(self,*args, **kwargs): 
        context = super(HomeView, self).get_context_data(*args,**kwargs) 
        context['banners'] = Banner.objects.all() 
        return context
    
class OrderSummaryView(View):

    def get(self,*args,**kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered = False)
            # print(order.order_items.item)
            context={
                'object': order
            }
            return render(self.request,'order_summary.html',context)
        except Exception as e:
            print(e)
            messages.error(self.request, message="you do not have active order ")
            return redirect('/')
        
class CheckoutView(View):

    def get(self,*args,**kwargs):
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered = False)
        context={
            'form': form,
            'order': order,
            'DISPLAY_COUPON_FORM': True
        }
        
        address = BillingAddress.objects.filter(user=self.request.user,default=True)
        if address.exists():
            context.update({
                'default_billing_address':address[0]
            })
        
        return render(self.request, 'checkout.html',context)
    
    def post(self,*args,**kwargs):
        form = CheckoutForm(self.request.POST or None)
        print(self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered = False)
            if form.is_valid():
                use_default_billing_address = form.cleaned_data.get('use_default_billing_address')
                if use_default_billing_address:
                    address = BillingAddress.objects.filter(user=self.request.user,default=True)
                    if address.exists():
                        billing_address = address[0]
                    else:
                        messages.info(self.request,'no default billing address is available')
                        return redirect("core:checkout.html")
                else:      
                    street_address = form.cleaned_data.get('billing_street_address')
                    appt_address = form.cleaned_data.get('billing_appt_address')
                    country = form.cleaned_data.get('billing_country')
                    zip = form.cleaned_data.get('billing_zip')
                    same_billing_address = form.cleaned_data.get('same_billing_address')
                    save_info = form.cleaned_data.get('save_info')
                    # payment_option = form.cleaned_data.get('payment_option')
                    billing_address = BillingAddress(user=self.request.user, street_address=street_address, appt_address=appt_address, country=country, zip=zip)
                    print('before if',save_info)
                    if save_info:
                        print('after if',save_info)
                        billing_address.default=True
                        billing_address.save()
                        
                    billing_address.save() 
                    order.billing_address=billing_address
                    
                    if same_billing_address:
                        shipping_address = ShippingAddress(user=self.request.user, street_address=street_address, appt_address=appt_address, country=country, zip=zip)
                        shipping_address.save()
                        order.shipping_address=shipping_address
                        # order.save()
                
                street_address = form.cleaned_data.get('shipping_street_address')
                appt_address = form.cleaned_data.get('shipping_appt_address')
                country = form.cleaned_data.get('shipping_country')
                zip = form.cleaned_data.get('shipping_zip')
                phone = form.cleaned_data.get('shipping_phone')
                email = form.cleaned_data.get('shipping_email')
                delivery_instructions = form.cleaned_data.get('shipping_delivery_instructions')

                shipping_address = ShippingAddress(user=self.request.user, street_address=street_address, appt_address=appt_address, country=country, zip=zip, phone=phone, email=email, delivery_instructions=delivery_instructions)
                shipping_address.save()
                order.shipping_address=shipping_address
                
                order.save()
                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == 'S':
                    return redirect('core:payment-view',payment_option="stripe")
                elif payment_option == 'P':
                    return redirect("core:payment-view",payment_option='paypal')
                else:
                    messages.warning(self.request, message='Invalid payment option selected')
                    return redirect('core:checkout')
                    
        except Exception as E:
            print(E)
            messages.warning(self.request, message="you do not have active order ")
            return redirect('core:order_summary')

class PaymentView(View):

    def get(self,*args,**kwargs):
        order=Order.objects.get(user=self.request.user,ordered=False)
        if order.billing_address:
            context={
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLICIABLE_KEY,
                'order':order,
                'DISPLAY_COUPON_FORM': False
                
            }
            return render(self.request, 'payment.html', context)
        else:
            messages.warning(self.request, message="you do not added an billing address ")
            return redirect('core:checkout')

    def post(self,*args,**kwargs):   
        try:
            # Use Stripe's library to make requests...
            order=Order.objects.get(user=self.request.user,ordered=False)
            token = self.request.POST.get('stripeToken')
            charge = stripe.Charge.create(
                amount=int(order.get_total()*100),
                currency="nzd",
                source=token,
                description="Living Life Wellington New Zealand",
                billing_details=order.billing_address,
                customer='Raj Lather'
                
            )
            payment = Payment(user=self.request.user, 
            stripe_charge_id=charge['id'],
            amount=order.get_total())
            payment.save()
            # TODO : 
            # WE HAVE TO MAKE ORDERED = TRUE FOR EVERY ITEM
            
            order.ordered=True
            order.payment=payment
            order.reference_code=create_reference_code()            
            order.save()
            messages.success(self.request, message="Order is succesfull & you will get email soon")
            return redirect('/')
        except stripe.error.CardError as e:
            # # Since it's a decline, stripe.error.CardError will be caught
            # print('Message is: %s' % e.user_message)
            messages.error(self.request, message=f'{e.user_message}')
            return redirect('/')
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, message="Rate Limit Error")
            return redirect('/')
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, message=f'{e} Invalid Parameters')
            return redirect('/')
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, message="Authentication Failed")
            return redirect('/')
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, message="Network error")
            return redirect('/')
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, message="Something went wrong, Please try again")
            return redirect('/')
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(self.request, message="serious issued occured, support team will back to you")
            return redirect('/')

            

def product_detail(request, slug):
    context = {
        'item': Item.objects.filter(slug=slug).first()
    }
    return render(request, 'product.html', context)

def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item,created = OrderItem.objects.get_or_create(item=item,user=request.user,ordered=False)

    order_qs = Order.objects.filter(user=request.user,ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.order_items.filter(item__slug=item.slug).exists():
            order_item.item_qty+=1
            order_item.save()
            messages.info(request, "Quantity of this item has been updated in your cart successfully")
            return redirect('core:order-summary')
        else:
            order.order_items.add(order_item)
            messages.info(request, "this item has been added in your cart successfully")
            return redirect('core:order-summary')
    else:
        ordered_date=timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.order_items.add(order_item)
        messages.info(request, "this item has been added in your cart successfully")
        return redirect('core:order-summary')


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.order_items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,user=request.user,ordered=False).first()
            order.order_items.remove(order_item)
            messages.info(request, "this item has been removed from the cart")
            return redirect('core:order-summary')
        else:
            messages.info(request, "this item is not in your cart")
            return redirect('core:product',slug=slug)
    else:
        messages.info(request, "You don't have any active order")
        return redirect('core:product',slug=slug)
    return redirect('core:product',slug=slug)

def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.order_items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,user=request.user,ordered=False).first()
            if order_item.item_qty >1:
                order_item.item_qty-=1
                order_item.save()
            else:
                order.order_items.remove(order_item)
            messages.info(request, "this item quantity has been updated")
            return redirect('core:order-summary')
        else:
            messages.info(request, "this item is not in your cart")
            return redirect('core:product',slug=slug)
    else:
        messages.info(request, "You don't have any active order")
        return redirect('core:product',slug=slug)
    return redirect('core:product',slug=slug)

def add_coupon(request):
    if request.method == 'POST':    
        try:
            order = Order.objects.get(user=request.user,ordered=False)
            coupon_code = request.POST.get('code')
            code = Coupon.objects.filter(code = coupon_code)
            if code.exists():
                order.coupon = code[0]
                order.save()
                messages.success(request, "Successfully Coupon added")
                return redirect('core:checkout')               
            else:
                messages.info(request, "This coupon does not exist")
                return redirect('core:checkout')             
        except ObjectDoesNotExist:
            messages.info(request, "You don't have any active order")
            return redirect('core:checkout')

class RequestRefundView(View):
    
    def get(self,*args,**kwargs):
        form = RefundForm()
        context={
            'form':form
        }
        return render(self.request, 'request_refund.html', context)
       
    def post(self,*args,**kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            reference_code = form.cleaned_data.get('reference_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')      
            try:
                order = Order.objects.get(reference_code=reference_code)
                order.request_refund = True
                order.save()
                refund = Refund()
                refund.order = order
                refund.message = message
                refund.email = email 
                refund.save()
                messages.info(self.request, message='Your refund request has been received')
                return redirect('core:request-refund')
            except ObjectDoesNotExist:
                messages.info(self.request, message='this order does not exist')
                return redirect('core:request-refund')
            
            
   
