from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserDetail

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username' : 'testusername',
            'password' : 'strongpassword123',
        }
        self.user = User.objects.create_user(**self.user_data)

        self.user_detail_data = {
            'user' : self.user,
            'first_name' : 'testfirst_name',
            'last_name' : 'testlast_name',
            'phone_number' : '123456789',
            'buyi' : '170',
            'vazni' : '80',
            'jinsi' : 'testjinsi',
            'maqsadi' : 'testmaqsadi',
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
        self.assertEqual(self.user.username,'testusername')
        self.assertTrue(self.user.check_password('strongpassword123'))

        self.assertEqual(self.user_detail.first_name,'testfirst_name')
        self.assertEqual(self.user_detail.last_name,'testlast_name')
        self.assertEqual(self.user_detail.phone_number,'123456789')
        self.assertEqual(self.user_detail.buyi,'170')
        self.assertEqual(self.user_detail.vazni,'80')
        self.assertEqual(self.user_detail.jinsi,'testjinsi')
        self.assertEqual(self.user_detail.maqsadi,'testmaqsadi')

    def test_user_str_representation(self):
        self.assertEqual(str(self.user),self.user.username)
        self.assertEqual(str(self.user_detail),f"{self.user.username} - Profili")