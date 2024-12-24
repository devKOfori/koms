from .. import models as api_models
from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken


class AuthenticationTest(TestCase):
    @classmethod
    def setUpTestData(self):
        male = api_models.Gender.objects.create(name="Male")
        system_user_data = {
            "username": "system_test_user",
            "first_name": "Test",
            "last_name": "User",
            "password": "secret",
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
        }
        api_models.CustomUser.objects.create_user(**system_user_data, gender=male)
        
        self.role = api_models.Role.objects.create(name="Headteacher")

    def setUp(self):
        # Create a user
        self.user = api_models.CustomUser.objects.get(username="system_test_user")
        # print(self.user)
        # Generate JWT tokens
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

    def test_register_url(self):
        register_url = reverse("register")
        self.assertEqual(register_url, "/v1/accounts/register/")

    def test_register_new_user(self):
        REGISTER_URL = reverse("register")
        self.new_user_data = {
            "user": {
                "username": "new_user",
                "first_name": "Test",
                "last_name": "User - New",
            },
            "residential_address": "John Doe Street.",
            "email": "test.newuser@domain.com",
            "password": "securepassword123",
            "roles": [
                # {"role": "8cefb839-208a-44a6-98f2-a545ed76d0a4"}
                {"role": self.role.id}
            ],
        }
        response = self.client.post(
            REGISTER_URL,
            data=self.new_user_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("full_name", response.data)
        self.assertEqual(
            response.data["full_name"],
            f"{self.new_user_data.get("user").get("first_name")} {self.new_user_data.get("user").get("last_name")}",
        )

    def test_logout_url(self):
        logout_url = reverse("logout")
        self.assertEqual(logout_url, "/v1/accounts/logout/")

    def test_logout(self):
        logout_url = reverse("logout")
        # print(f"Refresh token: {self.refresh.token}")
        response = self.client.post(
            logout_url,
            data={"refresh_token": str(self.refresh)},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(f"Response Content: {response.json()}")
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
        self.assertEqual(change_password_url, "/v1/accounts/change-password/")

    def test_change_password(self):
        change_password_url = reverse("change_password")
        response = self.client.post(
            change_password_url,
            data={"new_password": "new_user_password"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
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
        self.assertEqual("/v1/accounts/reset-password/", reverse("reset_password"))

    def test_reset_password(self):
        reset_password_url = reverse("reset_password")
        response = self.client.post(
            path=reset_password_url,
            content_type="application/json",
            data={"username": "system_test_user", "reset_channel": "email"},
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
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 400)