from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, View
from django.conf import settings
from django.http import HttpResponseRedirect

from .models import Banner, Item, Order, OrderItem, BillingAddress, Payment, Coupon, Refund, ShippingAddress,UserProfile
from .forms import CheckoutForm, RefundForm,CouponForm,PaymentForm

import random
import string

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
# stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"

# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token


# Create your views here.

def create_reference_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


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
            context={
                'object': order
            }
            return render(self.request,'order_summary.html',context)
        except Exception as e:
            print(e)
            messages.error(self.request, message="you do not have active order ")
            return redirect('/')
        
# class CheckoutView(View):

#     def get(self,*args,**kwargs):
#         form = CheckoutForm()
#         order = Order.objects.get(user=self.request.user, ordered = False)
#         context={
#             'form': form,
#             'order': order,
#             'DISPLAY_COUPON_FORM': True
#         }
        
#         address = BillingAddress.objects.filter(user=self.request.user,default=True)
#         if address.exists():
#             context.update({
#                 'default_billing_address':address[0]
#             })
        
#         return render(self.request, 'checkout.html',context)
    
#     def post(self,*args,**kwargs):
#         form = CheckoutForm(self.request.POST or None)
#         print(self.request.POST)
#         try:
#             order = Order.objects.get(user=self.request.user, ordered = False)
#             if form.is_valid():
#                 use_default_billing_address = form.cleaned_data.get('use_default_billing_address')
#                 if use_default_billing_address:
#                     address = BillingAddress.objects.filter(user=self.request.user,default=True)
#                     if address.exists():
#                         billing_address = address[0]
#                     else:
#                         messages.info(self.request,'no default billing address is available')
#                         return redirect("core:checkout.html")
#                 else:      
#                     street_address = form.cleaned_data.get('billing_street_address')
#                     appt_address = form.cleaned_data.get('billing_appt_address')
#                     country = form.cleaned_data.get('billing_country')
#                     zip = form.cleaned_data.get('billing_zip')
#                     same_billing_address = form.cleaned_data.get('same_billing_address')
#                     save_info = form.cleaned_data.get('save_info')
#                     # payment_option = form.cleaned_data.get('payment_option')
#                     billing_address = BillingAddress(user=self.request.user, street_address=street_address, appt_address=appt_address, country=country, zip=zip)
#                     print('before if',save_info)
#                     if save_info:
#                         print('after if',save_info)
#                         billing_address.default=True
#                         billing_address.save()
                        
#                     billing_address.save() 
#                     order.billing_address=billing_address
                    
#                     if same_billing_address:
#                         shipping_address = ShippingAddress(user=self.request.user, street_address=street_address, appt_address=appt_address, country=country, zip=zip)
#                         shipping_address.save()
#                         order.shipping_address=shipping_address
#                         # order.save()
                
#                 street_address = form.cleaned_data.get('shipping_street_address')
#                 appt_address = form.cleaned_data.get('shipping_appt_address')
#                 country = form.cleaned_data.get('shipping_country')
#                 zip = form.cleaned_data.get('shipping_zip')
#                 phone = form.cleaned_data.get('shipping_phone')
#                 email = form.cleaned_data.get('shipping_email')
#                 delivery_instructions = form.cleaned_data.get('shipping_delivery_instructions')

#                 shipping_address = ShippingAddress(user=self.request.user, street_address=street_address, appt_address=appt_address, country=country, zip=zip, phone=phone, email=email, delivery_instructions=delivery_instructions)
#                 shipping_address.save()
#                 order.shipping_address=shipping_address
                
#                 order.save()
#                 payment_option = form.cleaned_data.get('payment_option')
#                 if payment_option == 'S':
#                     return redirect('core:payment-view',payment_option="stripe")
#                 elif payment_option == 'P':
#                     return redirect("core:payment-view",payment_option='paypal')
#                 else:
#                     messages.warning(self.request, message='Invalid payment option selected')
#                     return redirect('core:checkout')
                    
#         except Exception as E:
#             print(E)
#             messages.warning(self.request, message="you do not have active order ")
#             return redirect('core:order_summary')

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid
    

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = ShippingAddress.objects.filter(
                user=self.request.user,
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = BillingAddress.objects.filter(
                user=self.request.user,
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = ShippingAddress.objects.filter(
                        user=self.request.user,
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = ShippingAddress(
                            user=self.request.user,
                            street_address=shipping_address1,
                            appt_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = BillingAddress(user=self.request.user, street_address=shipping_address1, appt_address=shipping_address2, country=shipping_country, zip=shipping_zip)
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = BillingAddress.objects.filter(
                        user=self.request.user,
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = BillingAddress(
                            user=self.request.user,
                            street_address=billing_address1,
                            appt_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment-view', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment-view', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


# class PaymentView(View):

#     def get(self,*args,**kwargs):
#         order=Order.objects.get(user=self.request.user,ordered=False)
#         if order.billing_address:
#             context={
#                 'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLICIABLE_KEY,
#                 'order':order,
#                 'DISPLAY_COUPON_FORM': False
                
#             }
#             return render(self.request, 'payment.html', context)
#         else:
#             messages.warning(self.request, message="you do not added an billing address ")
#             return redirect('core:checkout')

#     def post(self,*args,**kwargs):   
#         try:
#             # Use Stripe's library to make requests...
#             order=Order.objects.get(user=self.request.user,ordered=False)
#             token = self.request.POST.get('stripeToken')
#             print('token aa rha hai------------->',token)
#             amount = int(order.get_total() * 100)
#             charge = stripe.Charge.create(
#                         amount=amount,  # cents
#                         currency="usd",
#                         source=token
#                     )

#             payment = Payment(user=self.request.user, 
#             stripe_charge_id=charge['id'],
#             amount=order.get_total())
#             payment.save()
#             # TODO : 
#             # WE HAVE TO MAKE ORDERED = TRUE FOR EVERY ITEM
            
#             order.ordered=True
#             order.payment=payment
#             order.reference_code=create_reference_code()            
#             order.save()
#             messages.success(self.request, message="Order is succesfull & you will get email soon")
#             return redirect('/')
#         except stripe.error.CardError as e:
#             # # Since it's a decline, stripe.error.CardError will be caught
#             # print('Message is: %s' % e.user_message)
#             messages.error(self.request, message=f'{e.user_message}')
#             return redirect('/')
#         except stripe.error.RateLimitError as e:
#             # Too many requests made to the API too quickly
#             messages.error(self.request, message="Rate Limit Error")
#             return redirect('/')
#         except stripe.error.InvalidRequestError as e:
#             # Invalid parameters were supplied to Stripe's API
#             messages.error(self.request, message=f'{e} Invalid Parameters')
#             return redirect('/')
#         except stripe.error.AuthenticationError as e:
#             # Authentication with Stripe's API failed
#             # (maybe you changed API keys recently)
#             messages.error(self.request, message="Authentication Failed")
#             return redirect('/')
#         except stripe.error.APIConnectionError as e:
#             # Network communication with Stripe failed
#             messages.error(self.request, message="Network error")
#             return redirect('/')
#         except stripe.error.StripeError as e:
#             # Display a very generic error to the user, and maybe send
#             # yourself an email
#             messages.error(self.request, message="Something went wrong, Please try again")
#             return redirect('/')
#         except Exception as e:
#             # Something else happened, completely unrelated to Stripe
#             messages.error(self.request, f"serious issued occured, support team will back to you {e}")
#             return redirect('/')
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLICIABLE_KEY
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                print('--------------------->',card_list)
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            print(self.request.POST )
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    print(dir(customer))
                    # customer.create_source(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                        source=token
                    )
                    # customer.source = token
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="INR",
                        source=token,
                        # description = order.order_items.item.description
                        description = "test",
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                order_items = order.order_items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.ref_code = create_reference_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                print(e)
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")

            

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
            
            
   
