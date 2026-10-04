from datetime import date

from django import forms

from .models import FitnessPlan


class FitnessPlanForm(forms.ModelForm):
    class Meta:
        model = FitnessPlan
        fields = ['title', 'description', 'period_type', 'target_date', 'is_completed']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'period_type': forms.Select(attrs={'class': 'form-control'}),
            'target_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control', 'lang': 'uz'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Yangi rejada o'tgan sanani brauzer darajasida taqiqlaymiz.
        # Tahrirda eski sanani buzmaslik uchun min qo'yilmaydi.
        if not self.instance.pk:
            self.fields['target_date'].widget.attrs['min'] = date.today().isoformat()
