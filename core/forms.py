from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


PAYMENT_CHOICES=(
    ('S','Stripe'),
    ('P','Paypal')
    )

class CheckoutForm(forms.Form):
    billing_street_address = forms.CharField(widget=forms.TextInput(attrs={
        'id':'billing_address',
        'class':'form-control',
        'placeholder':'Please enter street address'
    }),required=False)
    billing_appt_address = forms.CharField(widget=forms.TextInput(attrs={
        'id':'billing_address-2 optional',
        'class':'form-control',
        'placeholder':'Please enter Apartment or suite or city'
    }),required=False)

    billing_country = CountryField(blank_label='(select a country)').formfield(widget=CountrySelectWidget(attrs={
        'id':'billing_country',
        'class':'custom-select d-block w-100'
    }),required=False)

    billing_zip = forms.CharField(widget=forms.TextInput(attrs={
        'id':'billing_zip',
        'class':'form-control',
        'type':'text'
    }),required=False)

    same_billing_address = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'id':'same_billing_address',
        'class':'custom-control-input',
        'type':'checkbox'
    }),required=False)

    save_info = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'id':'save_info',
        'class':'custom-control-input',
        'type':'checkbox'
    }),required=False)
    
    use_default_billing_address = forms.BooleanField(widget=forms.CheckboxInput(attrs={
        'id':'use_default_billing_address',
        'class':'custom-control-input',
        'type':'checkbox'
    }),required=False)

    shipping_street_address = forms.CharField(widget=forms.TextInput(attrs={
        'id':'shipping_address',
        'class':'form-control',
        'placeholder':'Please enter street address'
    }),required=False)
    shipping_appt_address = forms.CharField(widget=forms.TextInput(attrs={
        'id':'shipping_address-2 optional',
        'class':'form-control',
        'placeholder':'Please enter Apartment or suite or city'
    }),required=False)

    shipping_country = CountryField(blank_label='(select a country)').formfield(widget=CountrySelectWidget(attrs={
        'id':'shipping_country',
        'class':'custom-select d-block w-100'
    }),required=False)

    shipping_zip = forms.CharField(widget=forms.TextInput(attrs={
        'id':'shipping_zip',
        'class':'form-control',
        'type':'text'
    }),required=False)

    shipping_phone = forms.CharField(widget=forms.TextInput(attrs={
        'id':'shipping_phone',
        'class':'form-control',
        'placeholder':'Please enter phone number'
    }),required=False)
    shipping_email = forms.CharField(widget=forms.TextInput(attrs={
        'id':'shipping_email',
        'class':'form-control',
        'placeholder':'Please enter email'
    }),required=False)

    shipping_delivery_instructions = forms.CharField(widget=forms.TextInput(attrs={
        'id':'shipping_delivery_instructions',
        'class':'form-control',
        'placeholder':'Please enter delivery instructions'
    }),required=False)
    
    payment_option = forms.ChoiceField(widget=forms.RadioSelect,choices=PAYMENT_CHOICES)
    
       
class RefundForm(forms.Form):
    reference_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows':4
    }))
    email = forms.EmailField()
    
    
    