from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static


class UserDetail(models.Model):
    # Django'ning tayyor User modeli bilan One-to-One bog'lash
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profil',null=True,blank=True)
    telegram_user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='telegram_user',null=True,blank=True)
    avatar = models.ImageField(upload_to='avatar/', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    buyi = models.CharField(max_length=100, null=True, blank=True)
    vazni = models.CharField(max_length=100, null=True, blank=True)
    jinsi = models.CharField(max_length=100, null=True, blank=True)
    maqsadi = models.CharField(max_length=100, null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)


    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return static('images/default-avatar.png')

    @property
    def is_profile_coplete(self):
        return bool(self.buyi and self.vazni)

    def __str__(self):
        return f"{self.user.username} - Profili"


