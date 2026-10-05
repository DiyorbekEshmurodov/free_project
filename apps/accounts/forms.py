from django import forms
from django.core.exceptions import ValidationError
from .models import UserDetail
import re

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

    def clean_buyi(self):
        buyi = self.cleaned_data.get('buyi')
        if buyi is not None:
            if buyi < 50 or buyi > 250:
                raise ValidationError("Bo'yi 50 sm va 250 sm oralig'ida bo'lishi kerak!")
        return buyi

    def clean_vazni(self):
        vazni = self.cleaned_data.get('vazni')
        if vazni is not None:
            if vazni < 20 or vazni > 300:
                raise ValidationError("Vazni 20 kg va 300 kg oralig'ida bo'lishi kerak!")
        return vazni

    MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB
    ALLOWED_AVATAR_EXT = ('.jpg', '.jpeg', '.png', '.webp')

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        # Yangi fayl yuklangandagina tekshiramiz (mavjud/o'chirish holatida content_type yo'q)
        if avatar and hasattr(avatar, 'content_type'):
            if avatar.size > self.MAX_AVATAR_BYTES:
                raise ValidationError("Rasm hajmi 2 MB dan oshmasligi kerak!")
            if not avatar.name.lower().endswith(self.ALLOWED_AVATAR_EXT):
                raise ValidationError("Faqat JPG, PNG yoki WEBP rasm yuklash mumkin!")
        return avatar

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Очищаем от пробелов для корректной проверки
            phone_clean = phone.replace(" ", "").replace("-", "")
            phone_pattern = re.compile(r'^\+?[0-9]{9,15}$')
            if not phone_pattern.match(phone_clean):
                raise ValidationError("Noto'g'ri telefon raqami formati! Masalan: +998901234567")
        return phone