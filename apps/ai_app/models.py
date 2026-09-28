from django.db import models
from django.contrib.auth.models import User

class UserQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name="Savol sarlavhasi")
    text = models.TextField(null=True, blank=True, verbose_name="Savol matni")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"Savol #{self.id}"


class AICard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_cards', null=True, blank=True)
    question = models.ForeignKey(UserQuestion, on_delete=models.CASCADE, related_name='cards', null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name="Karta sarlavhasi")
    content = models.TextField(verbose_name="AI Javobi (Markdown)")
    section_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Bo'lim nomi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Kartasi"
        verbose_name_plural = "AI Kartalari"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


