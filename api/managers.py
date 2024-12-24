from django.contrib.auth.models import BaseUserManager
from django.db import transaction
from rest_framework import serializers
from . import models


def create_user_profile_with_roles(user, roles: list, **profile_details: dict):
    with transaction.atomic():
        user_profile = models.Profile.objects.create(user=user, **profile_details)
        for role in roles:
            models.ProfileRole.objects.create(
                profile=user_profile, role=role.get("role")
            )
    return user_profile


class CustomUserManager(BaseUserManager):
    def create_user(
        self, username, first_name, last_name, password=None, **extra_fields
    ):
        # Gather profile data
        profile_details = {}
        profile_details["full_name"] = f"{first_name} {last_name}"
        profile_details["birthdate"] = extra_fields.pop("birthdate", None)
        profile_details["phone_number"] = extra_fields.pop("phone_number", None)
        profile_details["gender"] = extra_fields.pop("gender", None)
        profile_details["residential_address"] = extra_fields.pop(
            "residential_address", None
        )
        profile_details["email"] = extra_fields.pop("email", None)
        roles = extra_fields.pop("roles", [])

        # Check if username field is provided
        if not username:
            raise ValueError("username field must be set")
        # Check if first_name field is provided
        if not first_name:
            raise ValueError("Firstname field must be set")
        # Check if last_name field is provided
        if not last_name:
            raise ValueError("Lastname field must be set")

        with transaction.atomic():
            # Create user and user profile
            user = self.model(
                username=username,
                first_name=first_name,
                last_name=last_name,
                **extra_fields,
            )
            user.set_password(password)
            user.save(using=self._db)

            user_profile = create_user_profile_with_roles(
                user, roles=roles, **profile_details
            )

        return user, user_profile

    def create_superuser(
        self, username, first_name, last_name, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields,
        )
