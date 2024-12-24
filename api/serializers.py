from rest_framework import serializers
from . import models
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from utils import generators, system_variables, notifications


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = ["username", "first_name", "last_name"]


class ProfileRolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileRole
        fields = ["role"]


class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PasswordReset
        fields = [
            "username",
            "user",
            "reset_channel",
            "date_created",
            "is_used",
            "expiry_date",
        ]
        read_only_fields = ["date_created", "is_used", "expiry_date", "user"]

    def validate_username(self, data):
        if not models.CustomUser.objects.filter(username=data).exists():
            raise serializers.ValidationError(
                {"error": "no account with the provided username exist"},
                code=status.HTTP_400_BAD_REQUEST,
            )

        return data

    def create(self, validated_data):
        print("Username in validated_data:", validated_data["username"])
        user_account = models.CustomUser.objects.get(
            username=validated_data.get("username")
        )
        user_profile = models.Profile.objects.get(user=user_account)
        reset_channel = validated_data.get("reset_channel")
        token = generators.generate_password_reset_token()

        with transaction.atomic():
            instance = models.PasswordReset.objects.create(
                user=user_account,
                token=token,
                is_used=False,
                reset_channel=reset_channel,
                expiry_date=timezone.now()
                + timedelta(
                    hours=system_variables.PASSWORD_RESET.get(
                        "RESET_TOKEN_EXPIRY_DURATION"
                    )
                ),
            )

            if reset_channel == "email":
                try:
                    if not user_profile.email:
                        raise serializers.ValidationError(
                            {"error": "user account has no email"}
                        )
                    notifications.send_email(
                        **system_variables.PASSWORD_RESET.get("RESET_LINK_EMAIL_CONF"),
                        to_email=[user_profile.email],
                    )
                except Exception as e:
                    raise serializers.ValidationError(
                        {"error": "Could not send token to your email"},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                try:
                    if not user_profile.phone_number:
                        raise serializers.ValidationError(
                            {"error": "user account has no phone number"}
                        )
                    notifications.send_SMS(
                        **system_variables.PASSWORD_RESET.get("RESET_LINK_EMAIL_CONF"),
                        to=user_profile.phone_number,
                    )
                except Exception as e:
                    raise serializers.ValidationError(
                        {"error": "Could not send token to phone number"},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
        return instance


class CustomUserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    roles = ProfileRolesSerializer(many=True)
    # created_by = serializers.SlugRelatedField(slug_field="full_name", queryset=models.Profile.objects.all())

    class Meta:
        model = models.Profile
        fields = [
            "full_name",
            "user",
            "department",
            "roles",
            "birthdate",
            "photo",
            "phone_number",
            "email",
            "residential_address",
            "gender",
            # "created_by",
        ]
        # read_only_fields = ["full_name", "created_by"]
        read_only_fields = ["full_name"]

    def create(self, validated_data):
        created_by = self.context["user_profile"]
        user_data = validated_data.pop("user")
        _, user_profile = models.CustomUser.objects.create_user(
            **user_data, **validated_data
        )
        return user_profile

    def update(self, instance, validated_data):
        user = instance.user
        user.username = validated_data.get("username", user.username)
        user.first_name = validated_data.get("first_name", user.first_name)
        user.last_name = validated_data.get("last_name", user.last_name)
        password = validated_data.get("password", None)
        if password:
            user.set_password(password)
        user.save()

        instance.birthdate = validated_data.get("birthdate", instance.birthdate)
        instance.photo = validated_data.get("photo", instance.photo)
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.address = validated_data.get("address", instance.address)
        instance.gender = validated_data.get("gender", instance.gender)

        # Update profile roles
        existing_roles = {role.id for role in instance.roles.all()}
        new_roles = validated_data.get("roles")
        models.ProfileRole.objects.filter(
            user=user, role__id__in=existing_roles - new_roles
        ).delete()

        instance.save()
        return instance
