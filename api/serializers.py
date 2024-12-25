from rest_framework import serializers
from . import models
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date, datetime
from utils import generators, system_variables, notifications, helpers


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = ["id", "username", "first_name", "last_name"]
        read_only_field = ["id"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_username(self, value):
        """
        Ensure the username is unique unless it belongs to the current instance.
        """
        user_id = self.instance.id if self.instance else None
        print(user_id)
        if (
            models.CustomUser.objects.filter(username=value)
            .exclude(id=user_id)
            .exists()
        ):
            raise serializers.ValidationError("User with this username already exists.")
        return value


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Role
        fields = ["id", "name"]


class ProfileRolesSerializer(serializers.ModelSerializer):
    role = RoleSerializer()

    class Meta:
        model = models.ProfileRole
        fields = ["id", "role", "is_active"]
        read_only_fields = ["id"]


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Gender
        fields = ["id", "name"]
        read_only_fields = ["id"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = ["id", "name"]
        read_only_fields = ["id"]


class CustomUserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    roles = ProfileRolesSerializer(many=True)
    department = DepartmentSerializer()
    gender = GenderSerializer()

    class Meta:
        model = models.Profile
        fields = [
            "id",
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
        ]
        read_only_fields = ["id", "full_name"]

    def create(self, validated_data):

        created_by = self.context["user_profile"]
        user_data = validated_data.pop("user")
        department_data = validated_data.pop("department")
        roles_data = validated_data.pop("roles")
        gender_data = validated_data.pop("gender")

        try:
            department = models.Department.objects.get(
                name__iexact=department_data.get("name")
            )
            gender = models.Gender.objects.get(name__iexact=gender_data.get("name"))
        except models.Department.DoesNotExist:
            raise serializers.ValidationError({"error": "invalid department provided"})
        except models.Gender.DoesNotExist:
            raise serializers.ValidationError({"error": "invalid gender provided"})

        with transaction.atomic():
            # create user account
            user = models.CustomUser.objects.create_user(**user_data)

            # create user profile
            user_profile = models.Profile.objects.create(
                user=user,
                full_name=f"{user_data.get('first_name')} {user_data.get('last_name')}",
                department=department,
                gender=gender,
                created_by=created_by,
                **validated_data,
            )

            roles = models.Role.objects.filter(
                name__in=[role_data["role"]["name"] for role_data in roles_data]
            )
            models.ProfileRole.objects.bulk_create(
                [
                    models.ProfileRole(profile=user_profile, role=role, is_active=True)
                    for role in roles
                ]
            )
        return user_profile

    def update(self, instance, validated_data):
        with transaction.atomic():
            # user = instance.user
            # user_data = validated_data.pop("user")
            # for attr, value in user_data.items():
            #     if attr == "username" and value != user.username:
            #         # Check if username already exists
            #         if models.CustomUser.objects.filter(username=value).exists():
            #             raise serializers.ValidationError(
            #                 {
            #                     "user": {
            #                         "username": "User with this username already exists."
            #                     }
            #                 }
            #             )
            #         if attr == "password":
            #             user.set_password(value)
            #     else:
            #         setattr(user, attr, value)
            # user.save()
            user = instance.user
            user_data = validated_data.pop("user", {})
            for attr, value in user_data.items():
                if attr == "username":
                    # Skip validation if the username is not changed
                    if value != user.username:
                        if models.CustomUser.objects.filter(username=value).exists():
                            raise serializers.ValidationError(
                                {
                                    "user": {
                                        "username": "User with this username already exists."
                                    }
                                }
                            )
                elif attr == "password":
                    user.set_password(value)
                else:
                    setattr(user, attr, value)
            user.save()
            existing_department = instance.department
            department_data = validated_data.pop("department")
            existing_gender = instance.gender
            gender_data = validated_data.pop("gender")
            try:
                new_department = models.Department.objects.get(
                    name=department_data.get("name")
                )
                instance.department = new_department or existing_department
                new_gender = models.Gender.objects.get(gender=gender_data.get("name"))
                instance.gender = new_gender or existing_gender
            except models.Department.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": "invalid department provided"}
                )
            except models.Gender.DoesNotExist:
                raise serializers.ValidationError({"error": "invalid gender provided"})

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Update roles
            roles_data = validated_data.pop("roles", [])
            if roles_data:
                # Clear existing roles and add new ones
                instance.roles.clear()
                roles = models.Role.objects.filter(
                    name__in=[role_data["role"]["name"] for role_data in roles_data]
                )
                models.ProfileRole.objects.bulk_create(
                    [
                        models.ProfileRole(
                            profile=instance,
                            role=role,
                            is_active=role_data.get("is_active", True),
                        )
                        for role, role_data in zip(roles, roles_data)
                    ]
                )

            return instance


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
        # print('Username in validated_data:', validated_data['username'])
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

            # if reset_channel == 'email':
            #     try:
            #         if not user_profile.email:
            #             raise serializers.ValidationError(
            #                 {'error': 'user account has no email'}
            #             )
            #         notifications.send_email(
            #             **system_variables.PASSWORD_RESET.get('RESET_LINK_EMAIL_CONF'),
            #             to_email=[user_profile.email],
            #         )
            #     except Exception as e:
            #         raise serializers.ValidationError(
            #             {'error': 'Could not send token to your email'},
            #             code=status.HTTP_400_BAD_REQUEST,
            #         )
            # else:
            #     try:
            #         if not user_profile.phone_number:
            #             raise serializers.ValidationError(
            #                 {'error': 'user account has no phone number'}
            #             )
            #         notifications.send_SMS(
            #             **system_variables.PASSWORD_RESET.get('RESET_LINK_EMAIL_CONF'),
            #             to=user_profile.phone_number,
            #         )
            #     except Exception as e:
            #         raise serializers.ValidationError(
            #             {'error': 'Could not send token to phone number'},
            #             code=status.HTTP_400_BAD_REQUEST,
            #         )
        return instance


class RoomKeepingAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RoomKeepingAssign
        fields = ["room", "shift", "assignment_date", "assigned_to"]

    def validate_assignment_date(self, data):
        if data < date.today():
            raise serializers.ValidationError(
                {"error": "Room Keeping Assignments cannot be saved for past dates"}
            )
        return data

    def create(self, validated_data):
        created_by = self.context.get("created_by")
        shift = validated_data.get("shift")
        assignment_date = validated_data.get("assignment_date")
        if not helpers.check_profile_department(created_by, "house keeping"):
            raise serializers.ValidationError(
                {"error": "User must be in house keeping to complete this action"},
                code=status.HTTP_400_BAD_REQUEST,
            )
        if not helpers.check_profile_role(created_by, "Supervisor"):
            raise serializers.ValidationError(
                {"error": "Only supervisors of housekeeping can complete this action"},
                code=status.HTTP_400_BAD_REQUEST,
            )
        if not helpers.check_user_shift(
            date=assignment_date,
            profile=validated_data.get("assigned_to"),
            shift_name=shift.name,
        ):
            raise serializers.ValidationError(
                {"error": f"The user has no {shift.name} on {assignment_date}"}
            )
        instance = models.RoomKeepingAssign.objects.create(
            **validated_data, created_by=created_by
        )
        return instance

    def update(self, instance, validated_data):
        modified_by = self.context.get("modified_by")
        instance.room = validated_data.get("room")
        instance.assignment_date = validated_data.get("assignment_date")
        instance.assigned_to = validated_data.get("assigned_to")
        instance.last_modified_by = modified_by
        instance.save()
        return instance
