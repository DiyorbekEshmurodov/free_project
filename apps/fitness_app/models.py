from django.db import models

from apps.accounts.models import UserDetail


class FitnessPlan(models.Model):
    PERIOD_CHOICES = (
        ('daily', 'Kunlik'),
        ('weekly', 'Haftalik'),
        ('monthly', 'Oylik'),
        ('yearly', 'Yillik'),
    )
    user = models.ForeignKey(UserDetail, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name="Reja nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name="Turi")
    target_date = models.DateField(verbose_name="Sana")
    is_completed = models.BooleanField(default=False, verbose_name="Bajarildi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            # plan_list: filter(user, period_type).order_by(target_date) uchun
            models.Index(fields=['user', 'period_type', 'target_date'], name='idx_plan_user_period_date'),
        ]
    def __str__(self):
        username = "Noma'lum"
        if self.user.user_id:
            username = self.user.user.username
        elif self.user.telegram_user_id:
            username = self.user.telegram_user.username
        return f"{username} - {self.title} ({self.period_type})"
