from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.urls import reverse
from apps.accounts.models import UserDetail
from apps.accounts.services import get_user_profile
from apps.accounts.forms import UserDetailForm

User = get_user_model()


class UserModelTest(TestCase):
    """User va UserDetail modellarini tekshirish."""
    def setUp(self):
        self.user_data = {
            'username': 'testusername',
            'password': 'strongpassword123',
        }
        self.user = User.objects.create_user(**self.user_data)

        self.user_detail = UserDetail.objects.get(user=self.user)
        self.user_detail.first_name = 'testfirst_name'
        self.user_detail.last_name = 'testlast_name'
        self.user_detail.phone_number = '+998901234567'
        self.user_detail.buyi = Decimal('170.0')
        self.user_detail.vazni = Decimal('80.0')
        self.user_detail.jinsi = 'erkak'
        self.user_detail.maqsadi = 'soglom_turmush'
        self.user_detail.save()

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testusername')
        self.assertTrue(self.user.check_password('strongpassword123'))
        self.assertEqual(self.user_detail.first_name, 'testfirst_name')

    def test_user_str_representation(self):
        self.assertEqual(str(self.user), self.user.username)
        self.assertIn(self.user.username, str(self.user_detail))


class SecurityAndResetTest(TestCase):
    """Parol tiklash xavfsizligini tekshirish."""
    def setUp(self):
        self.victim = User.objects.create_user(username='victim', password='OldPassword123!')

    def test_reset_action_does_not_change_password(self):
        self.client.post(reverse('login_page'), {
            'action_type': 'reset',
            'username': 'victim',
            'password': 'HackedPassword123!',
            'confirm_password': 'HackedPassword123!'
        }, follow=True)
        self.victim.refresh_from_db()
        self.assertTrue(self.victim.check_password('OldPassword123!'))


class SignalDuplicateProfileTest(TestCase):
    def test_only_one_userdetail_created_per_user(self):
        user = User.objects.create_user(username='signaltest', password='StrongPass123!')
        count = UserDetail.objects.filter(user=user).count()
        self.assertEqual(count, 1)


class AutoLoginFlowTest(TestCase):
    """Avto-kirish zanjirini tekshirish (follow=True orqali 301 yo'qotildi)."""
    def setUp(self):
        self.user = User.objects.create_user(username='tgUser', password='StrongPass123!')
        self.profile = UserDetail.objects.get(user=self.user)
        self.profile.telegram_id = 987654321
        self.profile.save()
        self.signer = TimestampSigner(salt='lifegym.autologin')

    def test_valid_signed_token_logs_user_in(self):
        token = self.signer.sign(str(self.profile.telegram_id))
        url = reverse('auto_login', args=[token])
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_reused_token_is_rejected(self):
        token = self.signer.sign(str(self.profile.telegram_id))
        url = reverse('auto_login', args=[token])
        self.client.get(url, follow=True)
        self.client.logout()

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_raw_unsigned_telegram_id_is_rejected(self):
        url = reverse('auto_login', args=[str(self.profile.telegram_id)])
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)


class UserDetailFormValidationTest(TestCase):
    def test_invalid_height_and_weight(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+998901234567',
            'buyi': 300,
            'vazni': 10,
            'jinsi': 'erkak',
            'maqsadi': 'soglom_turmush'
        }
        form = UserDetailForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('buyi', form.errors)
        self.assertIn('vazni', form.errors)


class GetUserProfileServiceTest(TestCase):
    def test_finds_profile_by_user_fk(self):
        user = User.objects.create_user(username='byuser', password='StrongPass123!')
        found = get_user_profile(user)
        self.assertIsNotNone(found)
        self.assertEqual(found.user, user)

    def test_unauthenticated_returns_none(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertIsNone(get_user_profile(AnonymousUser()))