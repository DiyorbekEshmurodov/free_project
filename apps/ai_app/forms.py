from django import forms
from .models import *
class UserForm(forms.ModelForm):
    class Meta:
        model = UserQuestion
        fields = '__all__'
        widgets = {
            'buyi': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Bo\'yingiz (sm)'}),
            'vazni': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Vazningiz (kg)'}),
            'maqsadi': forms.TextInput(attrs={'class': 'form-control'}),
        }
