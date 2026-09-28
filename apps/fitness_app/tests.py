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
        self.other_user = UserDetail.objects.get(user=self.other_user)

    def _get_url(self, name, *args):
        """URL oxirida slesh (/) bo'lishini kafolatlaydi."""
        url = reverse(name, args=args) if args else reverse(name)
        if not url.endswith('/'):
            url += '/'
        return url

    def test_hisobot_list(self):
        url = self._get_url('user_list')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hisobot_create(self):
        url = self._get_url('user_create')
        data = {
            'title': 'Yangi Reja Kiritish',
            'description': 'Test tavsifi',
            'period_type': 'daily',
            'target_date': str(date.today()),
            'is_completed': False
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hisobot_update(self):
        url = self._get_url('user_edit', self.hisobot.pk)
        data = {
            'title': 'Yangilangan Reja Nomi',
            'description': self.hisobot.description,
            'period_type': self.hisobot.period_type,
            'target_date': str(self.hisobot.target_date),
            'is_completed': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hisobot_delete(self):
        url = self._get_url('user_delete', self.hisobot.pk)
        response = self.client.post(url)
        print("DEBUG:", response.status_code, response.headers.get('Location'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(FitnessPlan.objects.filter(pk=self.hisobot.pk).count(), 0)

    def test_idor_protection_other_user_cannot_delete(self):
        self.client.force_login(self.other_user)
        url = self._get_url('user_delete', self.hisobot.pk)
        self.client.post(url, follow=True)
        self.assertEqual(FitnessPlan.objects.filter(pk=self.hisobot.pk).count(), 1)

    @patch('apps.fitness_app.views.ai_generate_advice')
    def test_ai_page_view(self, mock_advice):
        mock_advice.return_value = {
            'nutrition': 'Test', 'workout': 'Test',
            'ai_recommendation': 'Test', 'timeline': 'Test',
        }
        url = self._get_url('ai_page')
        response = self.client.get(url, {'card': 'weight_loss', 'period': 'weekly'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_advice.assert_called_once()