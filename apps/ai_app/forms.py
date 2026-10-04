from django import forms
from .models import UserQuestion
class UserForm(forms.ModelForm):
    class Meta:
        model = UserQuestion
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
