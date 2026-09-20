from django.db import models
from django.contrib.auth.models import User

class UserQuestion(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    buyi = models.IntegerField(null=True, blank=True)
    vazni = models.IntegerField(null=True, blank=True)
    maqsadi = models.CharField(max_length=100, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL,null=True, blank=True)


