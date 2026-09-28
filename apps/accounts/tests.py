from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.urls import reverse
from apps.accounts.models import UserDetail
from apps.accounts.services import get_user_profile

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testusername',
            'password': 'strongpassword123',
        }
        self.user = User.objects.create_user(**self.user_data)

        self.user_detail_data = {
            'user': self.user,
            'first_name': 'testfirst_name',
            'last_name': 'testlast_name',
            'phone_number': '123456789',
            # buyi/vazni endi DecimalField (avval CharField edi) — testda ham
            # sonli qiymat beriladi, matn emas.
            'buyi': Decimal('170.0'),
            'vazni': Decimal('80.0'),
            'jinsi': 'testjinsi',
            'maqsadi': 'testmaqsadi',
        }
        self.user_detail, created = UserDetail.objects.get_or_create(
            user=self.user,
            defaults=self.user_detail_data
        )
        if not created:
            for key, value in self.user_detail_data.items():
                setattr(self.user_detail, key, value)
            self.user_detail.save()

    def test_user_creation(self):
        # Username va Parol to'g'ri saqlanganini tekshirish
        self.assertEqual(self.user.username, 'testusername')
        self.assertTrue(self.user.check_password('strongpassword123'))

        # Profil ma'lumotlari mosligini tekshirish
        self.assertEqual(self.user_detail.first_name, 'testfirst_name')
        self.assertEqual(self.user_detail.last_name, 'testlast_name')
        self.assertEqual(self.user_detail.phone_number, '123456789')
        self.assertEqual(self.user_detail.buyi, Decimal('170.0'))
        self.assertEqual(self.user_detail.vazni, Decimal('80.0'))
        self.assertEqual(self.user_detail.jinsi, 'testjinsi')
        self.assertEqual(self.user_detail.maqsadi, 'testmaqsadi')

    def test_user_str_representation(self):
        # __str__ metodlari xatosiz matn qaytarishini tekshirish
        self.assertEqual(str(self.user), self.user.username)
        self.assertEqual(str(self.user_detail), f"{self.user.username} - Profili")


class SignalDuplicateProfileTest(TestCase):
    """1-bosqichda tuzatilgan 'ikkilangan UserDetail' bug'ining qaytadan
    paydo bo'lmasligini tekshiradi (regressiya himoyasi)."""

    def test_only_one_userdetail_created_per_user(self):
        user = User.objects.create_user(username='signaltest', password='StrongPass123')
        count = UserDetail.objects.filter(user=user).count()
        self.assertEqual(
            count, 1,
            "Bitta User uchun faqat bitta UserDetail yaratilishi kerak edi, "
            f"lekin {count} ta topildi (dublikat signal bug'i qaytgan bo'lishi mumkin)."
        )


class AutoLoginFlowTest(TestCase):
    """1-bosqichda tuzatilgan auto-login zanjirining (token imzolash +
    UserDetail.user to'ldirilishi) hozir ham to'g'ri ishlashini tekshiradi."""

    def setUp(self):
        self.user = User.objects.create_user(username='tgUser', password='StrongPass123')
        # Bot ro'yxatdan o'tkazganda qanday yozsa, xuddi shunday: telegram_id
        # BILAN BIRGA .user maydoni ham to'ldirilishi shart.
        self.profile = UserDetail.objects.filter(user=self.user).first()
        self.profile.telegram_id = 987654321
        self.profile.telegram_user = self.user
        self.profile.save()
        self.signer = TimestampSigner()

    def test_valid_signed_token_logs_user_in(self):
        token = self.signer.sign(str(self.profile.telegram_id))
        response = self.client.get(reverse('auto_login', args=[token]))
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_raw_unsigned_telegram_id_is_rejected(self):
        # 1-bosqichdagi asosiy bug: botda imzolanmagan xom ID yuborilgan edi.
        # Bunday token endi ham qabul qilinmasligi kerak (BadSignature).
        response = self.client.get(reverse('auto_login', args=[str(self.profile.telegram_id)]))
        self.assertRedirects(response, reverse('login_page'))

    def test_profile_without_user_field_cannot_login(self):
        # UserDetail.user bo'sh bo'lsa (eski bug holati), login berilmasligi kerak.
        self.profile.user = None
        self.profile.save()
        token = self.signer.sign(str(self.profile.telegram_id))
        response = self.client.get(reverse('auto_login', args=[token]))
        self.assertRedirects(response, reverse('login_page'))


class GetUserProfileServiceTest(TestCase):
    """apps/accounts/services.get_user_profile() ikkala FK (user, telegram_user)
    orqali ham profilni topa olishini tekshiradi."""

    def test_finds_profile_by_user_fk(self):
        user = User.objects.create_user(username='byuser', password='StrongPass123')
        found = get_user_profile(user)
        self.assertIsNotNone(found)
        self.assertEqual(found.user, user)

    def test_finds_profile_by_telegram_user_fk_when_user_fk_empty(self):
        user = User.objects.create_user(username='bytelegram', password='StrongPass123')
        profile = UserDetail.objects.filter(user=user).first()
        profile.user = None
        profile.telegram_user = user
        profile.save()
        found = get_user_profile(user)
        self.assertIsNotNone(found)
        self.assertEqual(found.telegram_user, user)

    def test_unauthenticated_returns_none(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertIsNone(get_user_profile(AnonymousUser()))