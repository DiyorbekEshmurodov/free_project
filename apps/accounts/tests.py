from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.signing import TimestampSigner
from django.test import TestCase
from django.urls import reverse

from apps.accounts.forms import UserDetailForm
from apps.accounts.models import UsedLoginToken, UserDetail
from apps.accounts.services import (
    UsernameTakenError,
    consume_login_token,
    get_user_profile,
    register_telegram_user,
)

User = get_user_model()


class CacheClearingTestCase(TestCase):
    """LocMemCache testlar orasida saqlanib qolmasligi uchun."""

    def setUp(self):
        super().setUp()
        cache.clear()


class MigrationConsistencyTest(CacheClearingTestCase):
    """PDF #1: migratsiyalar model sxemasiga to'liq mos bo'lishi shart."""

    def test_no_pending_model_changes(self):
        try:
            call_command('makemigrations', '--check', '--dry-run', stdout=StringIO(), stderr=StringIO())
        except SystemExit:
            self.fail("Modelda migratsiyasiz o'zgarish bor: makemigrations --check yiqildi.")

    def test_jinsi_and_maqsadi_are_real_columns(self):
        user = User.objects.create_user(username='schema_user', password='StrongPass123!')
        detail = UserDetail.objects.get(user=user)
        detail.jinsi = 'erkak'
        detail.maqsadi = 'soglom_turmush'
        detail.save()
        detail.refresh_from_db()
        self.assertEqual(detail.jinsi, 'erkak')
        self.assertEqual(detail.maqsadi, 'soglom_turmush')


class UserModelTest(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='testusername', password='strongpassword123')
        self.user_detail = UserDetail.objects.get(user=self.user)
        self.user_detail.first_name = 'testfirst_name'
        self.user_detail.last_name = 'testlast_name'
        self.user_detail.phone_number = '+998901234567'
        self.user_detail.buyi = 170.0
        self.user_detail.vazni = 80.0
        self.user_detail.jinsi = 'erkak'
        self.user_detail.maqsadi = 'soglom_turmush'
        self.user_detail.save()

    def test_user_creation(self):
        self.assertTrue(self.user.check_password('strongpassword123'))
        self.assertEqual(self.user_detail.first_name, 'testfirst_name')

    def test_str_representation(self):
        self.assertIn(self.user.username, str(self.user_detail))

    def test_str_without_user_does_not_crash(self):
        self.assertIn("Noma'lum", str(UserDetail.objects.create(telegram_id=1)))

    def test_profile_complete(self):
        self.assertTrue(self.user_detail.is_profile_complete)


class SecurityAndResetTest(CacheClearingTestCase):
    def test_reset_action_does_not_change_password(self):
        victim = User.objects.create_user(username='victim', password='OldPassword123!')
        self.client.post(reverse('login_page'), {
            'action_type': 'reset',
            'username': 'victim',
            'password': 'HackedPassword123!',
            'confirm_password': 'HackedPassword123!',
        }, follow=True)
        victim.refresh_from_db()
        self.assertTrue(victim.check_password('OldPassword123!'))

    def test_login_is_locked_after_five_failures(self):
        User.objects.create_user(username='locked', password='RightPass123!')
        for _ in range(5):
            self.client.post(reverse('login_page'),
                             {'action_type': 'login', 'username': 'locked', 'password': 'wrong'})
        self.client.post(reverse('login_page'),
                         {'action_type': 'login', 'username': 'locked', 'password': 'RightPass123!'})
        self.assertNotIn('_auth_user_id', self.client.session)


class SignalDuplicateProfileTest(CacheClearingTestCase):
    def test_only_one_userdetail_created_per_user(self):
        user = User.objects.create_user(username='signaltest', password='StrongPass123!')
        user.first_name = 'Changed'
        user.save()  # qayta saqlash ikkinchi profil yaratmasligi kerak
        self.assertEqual(UserDetail.objects.filter(user=user).count(), 1)


class AutoLoginFlowTest(CacheClearingTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='tgUser', password='StrongPass123!')
        self.profile = UserDetail.objects.get(user=self.user)
        self.profile.telegram_id = 987654321
        self.profile.save()
        self.signer = TimestampSigner(salt='lifegym.autologin')

    def _url(self, token):
        return reverse('auto_login', args=[token])

    def test_valid_signed_token_logs_user_in(self):
        token = self.signer.sign(str(self.profile.telegram_id))
        response = self.client.get(self._url(token))
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_reused_token_is_rejected(self):
        token = self.signer.sign(str(self.profile.telegram_id))
        self.client.get(self._url(token))
        self.client.logout()
        response = self.client.get(self._url(token))
        self.assertRedirects(response, reverse('login_page'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_reused_token_is_rejected_even_if_cache_is_empty(self):
        """Boshqa worker (bo'sh LocMemCache) holatini taqlid qiladi."""
        token = self.signer.sign(str(self.profile.telegram_id))
        self.client.get(self._url(token))
        self.client.logout()
        cache.clear()
        response = self.client.get(self._url(token))
        self.assertRedirects(response, reverse('login_page'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_raw_unsigned_telegram_id_is_rejected(self):
        response = self.client.get(self._url(str(self.profile.telegram_id)))
        self.assertRedirects(response, reverse('login_page'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_token_with_wrong_salt_is_rejected(self):
        bad = TimestampSigner(salt='other').sign(str(self.profile.telegram_id))
        self.client.get(self._url(bad))
        self.assertNotIn('_auth_user_id', self.client.session)


class ConsumeLoginTokenTest(CacheClearingTestCase):
    def test_token_is_consumed_only_once_across_cache_resets(self):
        self.assertTrue(consume_login_token('tok-1'))
        cache.clear()
        self.assertFalse(consume_login_token('tok-1'))
        self.assertTrue(consume_login_token('tok-2'))

    def test_raw_token_is_not_stored(self):
        consume_login_token('secret-token-value')
        self.assertFalse(UsedLoginToken.objects.filter(token_hash='secret-token-value').exists())
        self.assertEqual(len(UsedLoginToken.objects.get().token_hash), 64)


class TelegramRegistrationTest(CacheClearingTestCase):
    """PDF #2: username kolliziyasida begona hisob Telegram ID'ga bog'lanmasin."""
    DATA = {'first_name': 'Ali', 'last_name': 'Valiyev', 'phone_number': '+998901112233'}

    def test_new_user_is_registered_and_linked(self):
        user = register_telegram_user(111, 'newuser', 'StrongPass1', self.DATA)
        detail = UserDetail.objects.get(user=user)
        self.assertEqual(detail.telegram_id, 111)
        self.assertEqual(detail.phone_number, '+998901112233')
        self.assertTrue(user.check_password('StrongPass1'))
        self.assertEqual(UserDetail.objects.filter(user=user).count(), 1)

    def test_taken_username_is_rejected_and_victim_is_untouched(self):
        victim = User.objects.create_user(username='victim', password='VictimPass1')
        users_before = User.objects.count()

        with self.assertRaises(UsernameTakenError):
            register_telegram_user(555, 'victim', 'AttackerPass1', self.DATA)

        victim.refresh_from_db()
        self.assertTrue(victim.check_password('VictimPass1'))
        self.assertIsNone(UserDetail.objects.get(user=victim).telegram_id)
        self.assertFalse(UserDetail.objects.filter(telegram_id=555).exists())
        self.assertEqual(User.objects.count(), users_before)

    def test_attacker_signed_link_cannot_open_victim_session(self):
        User.objects.create_user(username='victim', password='VictimPass1')
        with self.assertRaises(UsernameTakenError):
            register_telegram_user(555, 'victim', 'AttackerPass1', self.DATA)

        token = TimestampSigner(salt='lifegym.autologin').sign('555')
        self.client.get(reverse('auto_login', args=[token]))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_already_linked_telegram_id_keeps_password(self):
        first = register_telegram_user(222, 'first', 'OriginalPass1', self.DATA)
        again = register_telegram_user(222, 'other', 'ChangedPass1', {'first_name': 'Yangi'})
        self.assertEqual(first.pk, again.pk)
        again.refresh_from_db()
        self.assertTrue(again.check_password('OriginalPass1'))
        self.assertEqual(again.first_name, 'Yangi')
        self.assertFalse(User.objects.filter(username='other').exists())

    def test_orphan_profile_with_telegram_id_is_attached_to_new_user(self):
        orphan = UserDetail.objects.create(telegram_id=777, first_name='Old')
        user = register_telegram_user(777, 'brandnew', 'StrongPass1', self.DATA)
        orphan.refresh_from_db()
        self.assertEqual(orphan.user, user)
        self.assertEqual(UserDetail.objects.filter(telegram_id=777).count(), 1)
        self.assertEqual(UserDetail.objects.filter(user=user).count(), 1)


class LogoutTest(CacheClearingTestCase):
    """PDF #6: logout faqat POST, UI esa CSRF tokenli forma ishlatadi."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='logoutuser', password='StrongPass123!')
        self.client.force_login(self.user)

    def test_get_logout_is_not_allowed(self):
        self.assertEqual(self.client.get(reverse('logout_page')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_post_logout_closes_session(self):
        response = self.client.post(reverse('logout_page'))
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_uses_post_form_with_csrf_token(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'method="post" action="/logout/"')
        self.assertContains(response, 'csrfmiddlewaretoken')


class ProfileSetupTest(CacheClearingTestCase):
    def test_profile_post_persists_jinsi_and_maqsadi(self):
        user = User.objects.create_user(username='profuser', password='StrongPass123!')
        self.client.force_login(user)
        response = self.client.post(reverse('profile_setup'), {
            'first_name': 'Ali', 'last_name': 'Valiyev', 'phone_number': '+998901234567',
            'buyi': '175', 'vazni': '70', 'jinsi': 'erkak', 'maqsadi': 'vazn_tashlash',
        })
        self.assertEqual(response.status_code, 302)
        detail = UserDetail.objects.get(user=user)
        self.assertEqual((detail.buyi, detail.vazni), (175.0, 70.0))
        self.assertEqual((detail.jinsi, detail.maqsadi), ('erkak', 'vazn_tashlash'))


class UserDetailFormValidationTest(CacheClearingTestCase):
    def test_invalid_height_and_weight(self):
        form = UserDetailForm(data={
            'first_name': 'Test', 'last_name': 'User', 'phone_number': '+998901234567',
            'buyi': 300, 'vazni': 10, 'jinsi': 'erkak', 'maqsadi': 'soglom_turmush',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('buyi', form.errors)
        self.assertIn('vazni', form.errors)


class GetUserProfileServiceTest(CacheClearingTestCase):
    def test_finds_profile_by_user_fk(self):
        user = User.objects.create_user(username='byuser', password='StrongPass123!')
        found = get_user_profile(user)
        self.assertIsNotNone(found)
        self.assertEqual(found.user, user)

    def test_unauthenticated_returns_none(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertIsNone(get_user_profile(AnonymousUser()))
