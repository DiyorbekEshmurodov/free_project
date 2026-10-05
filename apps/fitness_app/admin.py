from django.contrib import admin

from .models import FitnessPlan


@admin.register(FitnessPlan)
class FitnessPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'period_type', 'target_date', 'is_completed')
    list_filter = ('period_type', 'is_completed')
    # __str__ da user.user.username ishlatiladi: har qator uchun alohida so'rov (N+1) bo'lmasin
    list_select_related = ('user__user', 'user__telegram_user')
