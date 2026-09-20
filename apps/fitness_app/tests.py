from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from fitness_app.models import FitnessPlan
from accounts.models import UserDetail
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

        self.user_detail, _ = UserDetail.objects.get_or_create(
            user=self.user,
            defaults={
                'first_name': 'testfirst_name',
                'last_name': 'testlast_name',
                'phone_number': '123456789',
                'buyi': '170',
                'vazni': '80',
                'jinsi': 'testjinsi',
                'maqsadi': 'testmaqsadi',
            }
        )

        self.hisobot = FitnessPlan.objects.create(
            user=self.user_detail,  # UserDetail berildi
            title='Yangilangan Reja Nomi',
            description='Ertalabki 5 km yugurish',
            period_type='daily',
            target_date=date.today(),
            is_completed=False
        )



    def test_hisobot_list(self):
        url = reverse('user_list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND])


    def test_hisobot_detail(self):
        url = reverse('user_list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_302_FOUND])



    def test_hisobot_create(self):
        url = reverse('user_create')
        data = {
            'title': 'Yangi Reja',
            'description': 'Test tavsifi',
            'period_type': 'weekly',
            'target_date': str(date.today()),
            'is_completed': False
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code , status.HTTP_302_FOUND)
        self.assertEqual(FitnessPlan.objects.count(), 2)


    def test_hisobot_update(self):
        url = reverse('user_edit',args=[self.hisobot.pk])
        data = {
            'title': 'Yangilangan Reja Nomi',
            'description': self.hisobot.description,
            'period_type': self.hisobot.period_type,
            'target_date': str(self.hisobot.target_date),
            'is_completed': True
        }
        response = self.client.post(url,data,format='json')

        self.assertEqual(response.status_code , status.HTTP_302_FOUND)
        self.hisobot.refresh_from_db()
        self.assertEqual(self.hisobot.title,'Yangilangan Reja Nomi')

    def test_hisobot_delete(self):
        url = reverse('user_delete',args=[self.hisobot.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(FitnessPlan.objects.count(),0)

    @patch('fitness_app.views.AIPageDetailView.generate_user_advice')
    def test_ai_page_view(self, mock_generate_user_advice):
        mock_generate_user_advice.return_value = {
            "nutrition": "2L suv iching",
            "workout": "Mashqlarni bajaring",
            "ai_recommendation": "Yaxshi dam oling"
        }
        url = reverse('ai_page')  # URL nomingizga moslang
        response = self.client.get(url, {'card': 'weight_loss', 'period': 'weekly'})

        self.assertIn(response.status_code, [status.HTTP_200_OK,status.HTTP_302_FOUND])
