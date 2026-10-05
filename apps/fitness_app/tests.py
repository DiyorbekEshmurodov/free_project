import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import UserDetail
from apps.fitness_app import ai_api
from apps.fitness_app.models import FitnessPlan

User = get_user_model()

ADVICE = {'nutrition': 'N', 'workout': 'W', 'ai_recommendation': 'R', 'timeline': 'T'}


class FitnessBase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='testusername', password='strongpassword1234')
        self.detail = UserDetail.objects.get(user=self.user)
        self.detail.buyi, self.detail.vazni = 175.0, 70.0
        self.detail.save()

        self.plan = FitnessPlan.objects.create(
            user=self.detail, title='Yangilangan Reja Nomi', description='Ertalabki 5 km yugurish',
            period_type='daily', target_date=date.today(), is_completed=False,
        )

        self.other = User.objects.create_user(username='otheruser', password='PassWord123!')
        self.other_detail = UserDetail.objects.get(user=self.other)
        self.other_plan = FitnessPlan.objects.create(
            user=self.other_detail, title='Begona reja', period_type='daily', target_date=date.today(),
        )
        self.client.force_login(self.user)

    def payload(self, **extra):
        data = {
            'title': 'Yangi Reja', 'description': 'Tavsif', 'period_type': 'daily',
            'target_date': str(date.today()), 'is_completed': '',
        }
        data.update(extra)
        return data


class PlanCrudTests(FitnessBase):
    def test_list_shows_only_own_plans(self):
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['plans']), [self.plan])

    def test_create_plan(self):
        response = self.client.post(reverse('user_create'), self.payload(title='Mening rejam'))
        self.assertRedirects(response, reverse('user_list'), fetch_redirect_response=False)
        self.assertTrue(FitnessPlan.objects.filter(user=self.detail, title='Mening rejam').exists())

    def test_edit_plan(self):
        response = self.client.post(reverse('user_edit', args=[self.plan.pk]), self.payload(is_completed='on'))
        self.assertEqual(response.status_code, 302)
        self.plan.refresh_from_db()
        self.assertTrue(self.plan.is_completed)

    def test_delete_requires_post(self):
        url = reverse('user_delete', args=[self.plan.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertTrue(FitnessPlan.objects.filter(pk=self.plan.pk).exists())

    def test_delete_with_post(self):
        response = self.client.post(reverse('user_delete', args=[self.plan.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FitnessPlan.objects.filter(pk=self.plan.pk).exists())

    def test_other_user_cannot_delete_or_edit(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('user_delete', args=[self.plan.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('user_edit', args=[self.plan.pk]), self.payload()).status_code, 404)
        self.assertTrue(FitnessPlan.objects.filter(pk=self.plan.pk, title='Yangilangan Reja Nomi').exists())

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login_page'), response['Location'])

    def test_user_without_profile_is_sent_to_profile_setup(self):
        lonely = User.objects.create_user(username='lonely', password='StrongPass123!')
        UserDetail.objects.filter(user=lonely).delete()
        self.client.force_login(lonely)
        response = self.client.get(reverse('user_list'))
        self.assertRedirects(response, reverse('profile_setup'), fetch_redirect_response=False)

    def test_plan_str_is_safe(self):
        self.assertIn('testusername', str(self.plan))


class PaginationAndAdminTests(FitnessBase):
    def test_list_is_paginated(self):
        FitnessPlan.objects.bulk_create([
            FitnessPlan(user=self.detail, title=f'P{i}', period_type='daily', target_date=date.today())
            for i in range(24)
        ])  # setUp dagi 1 ta bilan jami 25 ta
        self.assertEqual(len(self.client.get(reverse('user_list')).context['plans']), 20)
        self.assertEqual(len(self.client.get(reverse('user_list'), {'page': 2}).context['plans']), 5)
        self.assertEqual(self.client.get(reverse('user_list'), {'page': 'abc'}).status_code, 200)

    def test_has_profile_context_for_logged_in_user(self):
        self.assertTrue(self.client.get(reverse('user_list')).context['has_profile'])

    def test_admin_changelist_loads(self):
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'AdminPass123!x')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:fitness_app_fitnessplan_changelist'))
        self.assertEqual(response.status_code, 200)


class AIPageTests(FitnessBase):
    @patch('apps.fitness_app.views.ai_generate_advice', return_value=ADVICE)
    def test_ai_page_view_passes_user_for_quota(self, mock_advice):
        response = self.client.get(reverse('ai_page'), {'card': 'weight_loss', 'period': 'weekly'})
        self.assertEqual(response.status_code, 200)
        mock_advice.assert_called_once()
        self.assertEqual(mock_advice.call_args.kwargs['user_id'], self.user.pk)

    @patch('apps.fitness_app.views.ai_generate_advice', return_value=ADVICE)
    def test_invalid_query_params_fall_back_to_whitelist(self, mock_advice):
        response = self.client.get(reverse('ai_page'), {'card': '<script>', 'period': 'x'})
        self.assertEqual(response.context['selected_card'], 'weight_loss')
        self.assertEqual(response.context['selected_period'], 'weekly')


class AIAdviceServiceTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_fallback_never_guarantees_results(self):
        for card in ('weight_loss', 'muscle_gain', 'stamina', 'health_habits'):
            for value in ai_api._fallback_advice(None, card, 'weekly').values():
                self.assertNotIn('kafolatlan', value.lower())
                self.assertNotIn('butunlay', value.lower())

    @override_settings(GROQ_API_KEY=None)
    def test_no_key_uses_fallback_without_model_call(self):
        with patch('apps.fitness_app.ai_api.cached_completion') as completion:
            result = ai_api.generate_user_advice(None, 'stamina', 'daily', user_id=1)
        completion.assert_not_called()
        self.assertEqual(set(result), set(ai_api.ADVICE_KEYS))

    @override_settings(GROQ_API_KEY='test-key')
    def test_valid_json_is_returned(self):
        with patch('apps.fitness_app.ai_api.cached_completion', return_value=json.dumps(ADVICE)):
            self.assertEqual(ai_api.generate_user_advice(None, 'stamina', 'daily', user_id=1), ADVICE)

    @override_settings(GROQ_API_KEY='test-key')
    def test_invalid_json_or_quota_message_uses_fallback(self):
        for bad in ('quota tugadi', '{"nutrition": 1}', ''):
            with patch('apps.fitness_app.ai_api.cached_completion', return_value=bad):
                result = ai_api.generate_user_advice(None, 'stamina', 'daily', user_id=1)
            self.assertEqual(set(result), set(ai_api.ADVICE_KEYS))
