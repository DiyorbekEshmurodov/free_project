from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserDetail


@receiver(post_save, sender=User, dispatch_uid='accounts.create_user_detail')
def create_user_detail(sender, instance, created, **kwargs):
    """Har yangi User uchun bitta UserDetail yaratadi."""
    if created:
        UserDetail.objects.get_or_create(user=instance)
