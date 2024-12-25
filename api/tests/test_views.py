from .. import models as api_models
from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken


class AuthenticationTest(TestCase):
    @classmethod
    def setUpTestData(self):
        self.male = api_models.Gender.objects.create(name="Male")
        self.female = api_models.Gender.objects.create(name="Female")
        self.housekeeping_dpt = api_models.Department.objects.create(
            name="House Keeping"
        )
        self.general_dpt = api_models.Department.objects.create(name="General")

        self.supervisor = api_models.Role.objects.create(name="Supervisor")
        self.admin = api_models.Role.objects.create(name="Admin")
        self.system_user_data = {
            "user": {
                "username": "system_user",
                "first_name": "System",
                "last_name": "Kempinski",
                "password": "secret",
            },
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
            "department": {"id": self.general_dpt.id, "name": self.general_dpt.name},
            "roles": [
                {
                    "id": "",
                    "role": {"id": self.admin.id, "name": self.admin.name},
                    "is_active": True,
                }
            ],
            "gender": {"id": self.male.id, "name": self.male.name},
        }

        # print(self.system_user_data)
        api_models.CustomUser.objects.create_user(**self.system_user_data.pop("user"))

    def setUp(self):
        # Create a user
        self.user = api_models.CustomUser.objects.get(username="system_user")
        self.system_user_profile = api_models.Profile.objects.create(
            user=self.user, full_name=f"{self.user.first_name} {self.user.last_name}"
        )
        self.housekeeping_dpt = api_models.Department.objects.get(name__iexact="house keeping")
        print(self.housekeeping_dpt.id)
        self.housekeeping_hod_user_data = {
            "user": {
                "username": "housekeeping_hod",
                "first_name": "hod housekeeping",
                "last_name": "kempinski",
                "password": "housekeeping_hod",
            },
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
            "department": {
                "name": self.housekeeping_dpt.name,
            },
            "roles": [
                {
                    "role": {"name": self.supervisor.name},
                    "is_active": True,
                }
            ],
            "gender": {"name": self.female.name},
        }

        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

    def test_register_url(self):
        register_url = reverse("register")
        self.assertEqual(register_url, "/koms/accounts/register/")

    def test_register_new_user(self):
        REGISTER_URL = reverse("register")
        response = self.client.post(
            REGISTER_URL,
            data=self.housekeeping_hod_user_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(f"response.data {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertIn("full_name", response.data)
        self.assertEqual(
            response.data["full_name"],
            f"{self.housekeeping_hod_user_data.get('user').get('first_name')} {self.housekeeping_hod_user_data.get('user').get('last_name')}",
        )
    def test_edit_user_profile(self):
        edit_profile_url = reverse('profile_details', kwargs={'pk', ''})
        response = self.client.post(
            edit_profile_url,
            data=self.housekeeping_hod_user_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(f"response.data {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertIn("full_name", response.data)
        self.assertEqual(
            response.data["full_name"],
            f"{self.housekeeping_hod_user_data.get('user').get('first_name')} {self.housekeeping_hod_user_data.get('user').get('last_name')}",
        )
    def test_logout_url(self):
        logout_url = reverse("logout")
        self.assertEqual(logout_url, "/koms/accounts/logout/")

    def test_logout(self):
        logout_url = reverse("logout")
        # print(f'Refresh token: {self.refresh.token}')
        response = self.client.post(
            logout_url,
            data={"refresh_token": str(self.refresh)},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        # print(f'Response Content: {response.json()}')
        self.assertEqual(response.status_code, 205)

    def test_logout_without_refresh_token(self):
        logout_url = reverse("logout")
        response = self.client.post(
            logout_url,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_url(self):
        change_password_url = reverse("change_password")
        self.assertEqual(change_password_url, "/koms/accounts/change-password/")

    def test_change_password(self):
        change_password_url = reverse("change_password")
        response = self.client.post(
            change_password_url,
            data={"new_password": "new_user_password"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(response.json())
        self.assertEqual(response.status_code, 200)

    def test_change_password_with_empty_password(self):
        change_password_url = reverse("change_password")
        response = self.client.post(
            change_password_url,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_reset_password_url(self):
        self.assertEqual("/koms/accounts/reset-password/", reverse("reset_password"))

    def test_reset_password(self):
        reset_password_url = reverse("reset_password")
        response = self.client.post(
            path=reset_password_url,
            content_type="application/json",
            data={"username": "system_user", "reset_channel": "email"},
        )
        print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 201)

    def test_reset_password_with_invalid_username(self):
        reset_password_url = reverse("reset_password")
        response = self.client.post(
            path=reset_password_url,
            content_type="application/json",
            data={"username": "system_test_user_1", "reset_channel": "email"},
        )
        # print(f'Response: {response.json()}')
        self.assertEqual(response.status_code, 400)

    def test_assign_housekeeping_url(self):
        assign_room_keeping_url = reverse("assign_room_keeping")
        self.assertEqual(assign_room_keeping_url, "/koms/assign-roomkeeping/")

    # def test_assign_roomkeeping_with_staff_member_account(self):
    #     assign_room_keeping_url = reverse("assign_room_keeping")
    #     response = self.client.post(path=assign_room_keeping_url, data={self})
