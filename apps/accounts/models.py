from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='detail', db_index=True,null=True,
        blank=True)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, db_index=True)
    telegram_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tg_detail')

    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    buyi = models.FloatField(null=True, blank=True)
    vazni = models.FloatField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['telegram_id'], name='idx_telegram_id'),
            models.Index(fields=['user'], name='idx_user_detail_user'),
        ]

    def __str__(self):
        return f"{self.user.username} Profili"


    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return static('images/default-avatar.png')

    @property
    def is_profile_complete(self):
        return bool(self.buyi and self.vazni)

    def __str__(self):
        return f"{self.user.username} - Profili"


