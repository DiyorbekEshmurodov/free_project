from django import forms
from datetime import date
from .models import FitnessPlan

class FitnessPlanForm(forms.ModelForm):
    class Meta:
        model = FitnessPlan
        fields = ['title', 'description', 'period_type', 'target_date', 'is_completed']
        ordering =['target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'type':'date',
            'min': date.today().isoformat(),  # Bugungi kundan oldingisini taqiqlaydi
            'lang': 'uz',
            'class': 'form-control'
        }
