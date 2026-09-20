from django.test import TestCase , Client
from django.contrib.auth import get_user_model
from accounts.models import UserDetail
from django.urls import reverse
from unittest.mock import patch
from ai_app.models import UserQuestion
from ai_app.prompts import SECTION_MAP

User = get_user_model()

class AIModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testusername',
            'password': 'strongpassword1234',
        }
        self.user = User.objects.create_user(**self.user_data)

        self.user_detail_data = {
            'user': self.user,
            'first_name': 'testfirst_name',
            'last_name': 'testlast_name',
            'phone_number': '123456789',
            'buyi': '170',
            'vazni': '80',
            'jinsi': 'testjinsi',
            'maqsadi': 'testmaqsadi',
        }
        self.user_detail , created = UserDetail.objects.get_or_create(
            user=self.user,
            defaults=self.user_detail_data
        )

        self.user_question_data = {
            'user': self.user,
            'buyi' : '170',
            'vazni' : '80',
            'maqsadi' : 'testmaqsadi'
        }
        self.user_question,created = UserQuestion.objects.get_or_create(
            user=self.user,
            defaults=self.user_question_data
        )

        if not created:
            for key , value in self.user_detail_data.items():
                setattr(self.user_detail , key , value)
            self.user_detail.save()

        self.client = Client()
        self.client.force_login(self.user)

    @patch('ai_app.views.ai_handler')
    def test_ai_response_with_user_profile(self,mock_ai_handler):
        mock_ai_handler.return_value = "AI maslahati: Har kuni 2 litr suv iching."

        first_section_name = list(SECTION_MAP.keys())[0]
        first_question_id = list(SECTION_MAP[first_section_name]['questions'].keys())[0]

        url = reverse(
            'card_detail', kwargs =
            {'section_name': first_section_name,
             'question_id': str(first_question_id)}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code,200)
        called_prompt = mock_ai_handler.call_args[0][0]
        self.assertIn("Bo'yi: 170 sm",called_prompt)
        self.assertIn("Vazni: 80 kg",called_prompt)



