from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.accounts.models import UserDetail
from django.urls import reverse
from unittest.mock import patch
from apps.ai_app.prompts import SECTION_MAP

User = get_user_model()


class AIModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testusername',
            'password': 'strongpassword1234',
        }
        self.user = User.objects.create_user(**self.user_data)

        # Signal yaratgan UserDetail obyekti olinadi va to'ldiriladi
        self.user_detail = UserDetail.objects.get(user=self.user)
        self.user_detail.first_name = 'testfirst_name'
        self.user_detail.last_name = 'testlast_name'
        self.user_detail.phone_number = '+998901234567'
        self.user_detail.buyi = 170
        self.user_detail.vazni = 80
        self.user_detail.jinsi = 'erkak'
        self.user_detail.maqsadi = 'testmaqsadi'
        self.user_detail.save()

        self.client = Client()
        self.client.force_login(self.user)

    def test_ai_response_with_user_profile(self):
        """AI karta tafsilotlari sahifasi yuklanishini tekshirish."""
        first_section_name = list(SECTION_MAP.keys())[0]
        first_question_id = list(SECTION_MAP[first_section_name]['questions'].keys())[0]

        url = reverse(
            'card_detail', kwargs={
                'section_name': first_section_name,
                'question_id': str(first_question_id)
            }
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)