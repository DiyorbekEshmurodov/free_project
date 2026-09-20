from django import forms
from .models import UserDetail

class UserDetailForm(forms.ModelForm):
    MAQSAD_CHOICES = [
        ('', '--- Maqsadni tanlang ---'),
        ('vazn_tashlash', 'Vazn tashlash (Ozish)'),
        ('vazn_yigish', "Vazn yig'ish (Semirish)"),
        ('mushak_chiqarish', 'Mushak massasini oshirish'),
        ('soglom_turmush', "Sog'lom turmush tarzi"),
    ]

    JINSI_CHOICES = [
        ('erkak', 'Erkak'),
        ('ayol', 'Ayol'),
    ]

    maqsadi = forms.ChoiceField(
        choices=MAQSAD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    jinsi = forms.ChoiceField(
        choices=JINSI_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'})
    )

    class Meta:
        model = UserDetail
        fields = ['first_name', 'last_name', 'phone_number', 'buyi', 'vazni', 'jinsi', 'maqsadi','avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ismingiz'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Familiyangiz'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+998 90 123 45 67'}),
            'buyi': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Masalan: 175'}),
            'vazni': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Masalan: 70'}),
        }