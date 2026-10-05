from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.ai_app.llm import (
    NO_KEY_MESSAGE,
    QUOTA_MESSAGE,
    UNAVAILABLE_MESSAGE,
    cached_completion,
)
from apps.ai_app.prompts import SECTION_MAP

User = get_user_model()


class AICardsViewTests(TestCase):
    """PDF #3: cards_list URL kwarg (section_name) va view mos bo'lishi shart."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='aiuser', password='StrongPass123!')
        self.client.force_login(self.user)

    def test_url_contract(self):
        self.assertEqual(reverse('cards_list', kwargs={'section_name': 'nutrition'}), '/ai_app/nutrition/')

    def test_cards_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('cards_list', kwargs={'section_name': 'nutrition'}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login_page'), response['Location'])

    def test_cards_list_ok_for_every_section(self):
        for section_name in SECTION_MAP:
            with self.subTest(section=section_name):
                response = self.client.get(reverse('cards_list', kwargs={'section_name': section_name}))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'ai_app/cards.html')
                self.assertEqual(response.context['section_name'], section_name)

    def test_cards_list_unknown_section_is_404(self):
        response = self.client.get(reverse('cards_list', kwargs={'section_name': 'yoq_bolim'}))
        self.assertEqual(response.status_code, 404)

    @patch('apps.ai_app.views.get_cached_llm_completion', return_value='Test javob')
    def test_card_detail_ok_for_every_question(self, mock_llm):
        for section_name, section in SECTION_MAP.items():
            for question_id in section['questions']:
                with self.subTest(section=section_name, question=question_id):
                    url = reverse('card_detail', kwargs={'section_name': section_name, 'question_id': question_id})
                    self.assertEqual(self.client.get(url).status_code, 200)

    @patch('apps.ai_app.views.get_cached_llm_completion', return_value='x')
    def test_card_detail_unknown_question_is_404(self, mock_llm):
        url = reverse('card_detail', kwargs={'section_name': 'nutrition', 'question_id': 'q999'})
        self.assertEqual(self.client.get(url).status_code, 404)
        mock_llm.assert_not_called()

    @patch('apps.ai_app.views.get_cached_llm_completion', return_value='Test javob')
    def test_card_detail_passes_user_id_for_quota(self, mock_llm):
        url = reverse('card_detail', kwargs={'section_name': 'nutrition', 'question_id': 'q1'})
        self.client.get(url)
        self.assertEqual(mock_llm.call_args.kwargs['user_id'], self.user.pk)


def _fake_client(content='javob'):
    """Groq klientining soxta nusxasi (tarmoqqa chiqmaydi)."""
    client = SimpleNamespace()
    client.chat = SimpleNamespace(completions=SimpleNamespace())
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    client.chat.completions.create = create
    return client, calls


MSG = [{"role": "user", "content": "salom"}]


@override_settings(GROQ_API_KEY='test-key', AI_DAILY_LIMIT=2)
class AIQuotaTests(TestCase):
    """PDF #7: foydalanuvchi kvotasi va kesh; limitdan keyin model chaqirilmaydi."""

    def setUp(self):
        cache.clear()

    def test_model_is_not_called_after_limit(self):
        client, calls = _fake_client()
        with patch('apps.ai_app.llm.get_client', return_value=client):
            r1 = cached_completion('t', 'p1', MSG, user_id=1)
            r2 = cached_completion('t', 'p2', MSG, user_id=1)
            r3 = cached_completion('t', 'p3', MSG, user_id=1)
        self.assertEqual((r1, r2), ('javob', 'javob'))
        self.assertEqual(r3, QUOTA_MESSAGE)
        self.assertEqual(len(calls), 2)

    def test_quota_is_per_user(self):
        client, calls = _fake_client()
        with patch('apps.ai_app.llm.get_client', return_value=client):
            cached_completion('t', 'a', MSG, user_id=1)
            cached_completion('t', 'b', MSG, user_id=1)
            other = cached_completion('t', 'c', MSG, user_id=2)
        self.assertEqual(other, 'javob')

    def test_cached_answer_costs_nothing(self):
        client, calls = _fake_client()
        with patch('apps.ai_app.llm.get_client', return_value=client):
            for _ in range(5):
                cached_completion('t', 'same', MSG, user_id=1)
            fresh = cached_completion('t', 'other', MSG, user_id=1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(fresh, 'javob')

    def test_model_error_returns_safe_message_and_logs(self):
        client, _ = _fake_client()

        def boom(**kwargs):
            raise RuntimeError('groq down')

        client.chat.completions.create = boom
        with patch('apps.ai_app.llm.get_client', return_value=client):
            with self.assertLogs('apps.ai_app.llm', level='ERROR'):
                result = cached_completion('t', 'p', MSG, user_id=1)
        self.assertEqual(result, UNAVAILABLE_MESSAGE)

    @override_settings(GROQ_API_KEY=None)
    def test_missing_key_does_not_call_model(self):
        with patch('apps.ai_app.llm.get_client') as get_client:
            self.assertEqual(cached_completion('t', 'p', MSG, user_id=1), NO_KEY_MESSAGE)
            get_client.assert_not_called()


class QuotaFailClosedTests(TestCase):
    """R2: user_id unutilsa kvota jimgina o'chib qolmasligi kerak."""

    def setUp(self):
        cache.clear()

    def test_consume_quota_without_user_raises(self):
        from apps.ai_app.llm import consume_quota
        with self.assertRaises(ValueError):
            consume_quota(None)

    def test_cached_completion_requires_user_id(self):
        with self.assertRaises(TypeError):
            cached_completion('t', 'p', MSG)  # user_id berilmagan
