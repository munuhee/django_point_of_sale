# forms.py
from django import forms
from .models import Tax

class TaxForm(forms.ModelForm):
    class Meta:
        model = Tax
        fields = ['percentage', 'status']
