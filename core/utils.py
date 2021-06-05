from django.core.mail import send_mail, EmailMessage
from .models import ShippingAddress
from django.contrib.auth.models import User
from django.template.loader import get_template

def send_mail_to_customer(request,order):
    total=int(order.get_total())+40
    address=order.shipping_address
    
    context = {
        'reference_code':order.reference_code,
        'customer_name':request.user.username,
        'customer_address':address.street_address+' '+address.appt_address+' '+address.zip,
        'sub_total':order.get_total(),
        'delivery_charges':40,
        'grant_total':total
    }
    message=get_template(template_name='order_confirmation.html').render(context)
    msg=EmailMessage(
        'your Next Life Style Order',
        message,
        'krishna.devi0107@gmail.com',
        [f'{request.user.email}'],
    )
    msg.content_subtype="html"
    msg.send()
    print('mail sent successfully')
    
    
        
    
