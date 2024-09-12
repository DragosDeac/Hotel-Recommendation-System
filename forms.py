from django import forms
from .models import Sejur

class SejurForm(forms.ModelForm):
    class Meta:
        model = Sejur
        fields = ['hotel', 'start_date', 'end_date', 'number_of_people']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }