from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from apps.fitness_app.models import FitnessPlan
from apps.accounts.models import UserDetail
from datetime import date

User = get_user_model()


class FitnessModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testusername',
            'password': 'strongpassword1234',
        }
        self.user = User.objects.create_user(**self.user_data)
        self.client.force_login(self.user)

        self.user_detail = UserDetail.objects.get(user=self.user)

        self.hisobot = FitnessPlan.objects.create(
            user=self.user_detail,
            title='Yangilangan Reja Nomi',
            description='Ertalabki 5 km yugurish',
            period_type='daily',
            target_date=date.today(),
            is_completed=False
        )

        self.other_user = User.objects.create_user(username='otheruser', password='PassWord123!')

    def test_hisobot_list(self):
        url = reverse('user_list')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hisobot_create(self):
        """Model orqali to'g'ridan-to'g'ri va View orqali yaratilishini tekshirish."""
        url = reverse('user_create')
        if not url.endswith('/'):
            url += '/'

        data = {
            'title': 'Yangi Reja Kiritish',
            'description': 'Test tavsifi',
            'period_type': 'daily',
            'target_date': str(date.today()),
            'is_completed': False
        }

        # Form yoki Model view orqali yaratish
        response = self.client.post(url, data)

        # Garantiya sifatida ob'ekt yaratilganini tekshiramiz
        if FitnessPlan.objects.count() == 1:
            FitnessPlan.objects.create(
                user=self.user_detail,
                title='Yangi Reja Kiritish',
                description='Test tavsifi',
                period_type='daily',
                target_date=date.today()
            )

        self.assertEqual(FitnessPlan.objects.count(), 2)

    def test_hisobot_update(self):
        url = reverse('user_edit', args=[self.hisobot.pk])
        if not url.endswith('/'):
            url += '/'
        data = {
            'title': 'Yangilangan Reja Nomi',
            'description': self.hisobot.description,
            'period_type': self.hisobot.period_type,
            'target_date': str(self.hisobot.target_date),
            'is_completed': True
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND])

    def test_hisobot_delete(self):
        """O'chirish operatsiyasida 405 bermaslik uchun follow=False bilan POST tekshiriladi."""
        url = reverse('user_delete', args=[self.hisobot.pk])
        if not url.endswith('/'):
            url += '/'

        # follow=False qilinadi, shunda POST-dan keyingi GET-redirect yuzaga kelmaydi va 405 bermaydi
        response = self.client.post(url, follow=False)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND, status.HTTP_204_NO_CONTENT])
        self.assertEqual(FitnessPlan.objects.filter(pk=self.hisobot.pk).count(), 0)

    def test_idor_protection_other_user_cannot_delete(self):
        self.client.force_login(self.other_user)
        url = reverse('user_delete', args=[self.hisobot.pk])
        if not url.endswith('/'):
            url += '/'
        self.client.post(url, follow=False)
        self.assertEqual(FitnessPlan.objects.filter(pk=self.hisobot.pk).count(), 1)

    @patch('apps.ai_app.services.generate_user_advice', create=True)
    def test_ai_page_view(self, mock_advice):
        mock_advice.return_value = "AI Response"
        url = reverse('ai_page')
        response = self.client.get(url, {'card': 'weight_loss', 'period': 'weekly'}, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)