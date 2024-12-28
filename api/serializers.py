from rest_framework import serializers
from . import models
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from datetime import timedelta, date, datetime
from utils import generators, system_variables, notifications, helpers


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_username(self, value):
        print("here.......")
        user_model = get_user_model()
        request = self.context.get(
            "request"
        )  # Get the request from the serializer context
        # if request and request.method in ['PUT', 'PATCH']:
        if self.instance:
            # Exclude the current user from the uniqueness check
            if (
                user_model.objects.filter(username=value)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "User with this username already exists."
                )
        else:
            # For creation, ensure the username is unique
            if user_model.objects.filter(username=value).exists():
                raise serializers.ValidationError(
                    "User with this username already exists."
                )
        return value


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Role
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if models.Role.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                {"error": "A role with the same name already exist"}
            )
        return value

    def create(self, validated_data):
        with transaction.atomic():
            role = models.Role.objects.create(**validated_data)
            # create corresponding group
            Group.objects.get_or_create(**validated_data)
        return role

    def update(self, instance, validated_data):
        with transaction.atomic():
            old_name = instance.name
            new_name = validated_data.get("name")
            instance.name = new_name
            instance.save()
            if old_name != new_name:
                try:
                    group = Group.objects.get(name=old_name)
                    group.name = new_name
                    group.save()
                except Group.DoesNotExist:
                    Group.objects.create(name=new_name)
        return instance


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if models.Department.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                {"error": "A department with the same name exist"}
            )
        return value

    def create(self, validated_data):
        with transaction.atomic():
            department = models.Department.objects.create(**validated_data)
            # create corresponding group
            Group.objects.get_or_create(**validated_data)
        return department

    def update(self, instance, validated_data):
        with transaction.atomic():
            old_name = instance.name
            new_name = validated_data.get("name")
            instance.name = new_name
            instance.save()
            if old_name != new_name:
                try:
                    group = Group.objects.get(name=old_name)
                    group.name = new_name
                    group.save()
                except Group.DoesNotExist:
                    Group.objects.create(name=new_name)
        return instance


class ProfileRolesSerializer(serializers.ModelSerializer):
    # role = RoleSerializer()
    role = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Role.objects.all()
    )

    class Meta:
        model = models.ProfileRole
        fields = ["id", "role", "is_active"]
        read_only_fields = ["id"]


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Gender
        fields = ["id", "name"]
        read_only_fields = ["id"]


# class DepartmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Department
#         fields = ['id', 'name']
#         read_only_fields = ['id']


class CustomUserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    roles = ProfileRolesSerializer(many=True)
    department = serializers.CharField(max_length=255)
    gender = serializers.CharField(max_length=255)

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
            #     department_name = department_data.get('name')
            department = models.Department.objects.get(name__iexact=department_data)
            gender = models.Gender.objects.get(name__iexact=gender_data)
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
            roles = [role_data["role"] for role_data in roles_data]
            # models.ProfileRole.objects.bulk_create(
            #     [
            #         models.ProfileRole(profile=user_profile, role=role, is_active=True)
            #         for role in roles
            #     ]
            # )
            # build a list containing the names of roles and dept which is used to search for the groups to which the user is added
            group_names_list = [role.name for role in roles]
            group_names_list.append(department_data)
            # set profile roles
            helpers.set_profile_roles(profile=user_profile, roles_data=roles_data)
            # set profile groups
            helpers.set_profile_groups(
                profile=user_profile, group_names_list=group_names_list
            )

        return user_profile

    def update(self, instance, validated_data):
        with transaction.atomic():
            print("here.....999..")
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
                    name__iexact=department_data
                )
                instance.department = new_department or existing_department
                new_gender = models.Gender.objects.get(gender=gender_data)
                instance.gender = new_gender or existing_gender
            except models.Department.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": "invalid department provided"}
                )
            except models.Gender.DoesNotExist:
                raise serializers.ValidationError({"error": "invalid gender provided"})

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            full_name = f"{user_data.get('first_name')} {user_data.get('last_name')}"
            instance.full_name = full_name or instance.full_name
            instance.save()

            # Update roles
            roles_data = validated_data.pop("roles", [])
            if roles_data:
                # Clear existing roles and add new ones
                # instance.roles.clear()
                # roles = models.Role.objects.filter(
                #     name__in=[role_data['role'] for role_data in roles_data]
                # )
                helpers.set_profile_roles(profile=instance, roles_data=roles_data)
                roles = [role_data["name"] for role_data in roles_data]
                # models.ProfileRole.objects.bulk_create(
                #     [
                #         models.ProfileRole(
                #             profile=instance,
                #             role=role,
                #             is_active=role_data.get('is_active', True),
                #         )
                #         for role, role_data in zip(roles, roles_data)
                #     ]
                # )
                group_names_list = [role.name for role in roles]
                group_names_list.append(department_data)
                helpers.set_profile_groups(
                    profile=instance, group_names_list=group_names_list
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


class ProfileShiftAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProfileShiftAssign
        fields = ["id", "profile", "shift", "date"]
        read_only_fields = ["id"]

    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                {"error": "you are trying to assign a shift for a past date."}
            )
        return value

    def validate(self, attrs):
        created_by = self.context.get("created_by")
        modified_by = self.context.get("modified_by")
        author = created_by or modified_by
        profile = attrs.get("profile")

        if not author:
            raise serializers.ValidationError(
                {"error": "The user trying to create the shift has no profile."}
            )

        # Validation 1: Ensure the profile is in the same department
        if profile.department != author.department:
            raise serializers.ValidationError(
                {
                    "error": "The user you are trying to assign a shift to is not in your department."
                }
            )

        # Validation 2: Check if the user has the correct role to assign shifts
        if not author.roles.exclude(role__name__iexact="staff").exists():
            raise serializers.ValidationError(
                {
                    "error": "Your account role does not have the authorization to perform this action"
                }
            )

        # Validation 3: Prevent duplicate assignments for the same shift on the same day
        if models.ProfileShiftAssign.objects.filter(
            profile=profile, shift=attrs.get("shift"), date=attrs.get("date")
        ).exists():
            raise serializers.ValidationError(
                {
                    "error": "You cannot assign the same shift to the same person on the same day."
                }
            )

        return attrs

    def create(self, validated_data):
        created_by = self.context.get("created_by")
        department = created_by.department
        return models.ProfileShiftAssign.objects.create(
            department=department, created_by=created_by, **validated_data
        )

    def update(self, instance, validated_data):
        modified_by = self.context.get("modified_by")
        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)
        instance.modified_by = modified_by
        instance.save()
        return instance


class RoomKeepingAssignSerializer(serializers.ModelSerializer):
    room = serializers.SlugRelatedField(
        slug_field="room_number", queryset=models.Room.objects.all()
    )
    shift = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Shift.objects.all()
    )
    # assigned_to = serializers.SlugRelatedField(slug_field='assigned_to__username')

    class Meta:
        model = models.RoomKeepingAssign
        fields = ["id", "room", "shift", "assignment_date", "assigned_to"]
        read_only_fields = ["id"]

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
        instance.room = validated_data.get("room", instance.room)
        instance.assignment_date = validated_data.get("assignment_date", instance.assignment_date)
        instance.assigned_to = validated_data.get("assigned_to", instance.assigned_to)
        instance.last_modified_by = modified_by
        instance.save()
        return instance


class ProcessRoomKeepingSerializer(serializers.ModelSerializer):
    room_state_trans = serializers.SlugRelatedField(
        slug_field="final_trans_state",
        queryset=models.HouseKeepingStateTrans.objects.all(),
    )
    shift = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Shift.objects.all()
    )
    room = serializers.SlugRelatedField(
        slug_field="room_number", queryset=models.Room.objects.all()
    )

    class Meta:
        model = models.ProcessRoomKeeping
        fields = [
            "id",
            "room_keeping_assign",
            "room",
            "room_state_trans",
            "date_processed",
            "shift",
            "note",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "shift",
            "created_by",
            "room",
        ]

    def validate(self, attrs):
        room_state_trans = attrs.get("room_state_trans")
        final_trans_state = room_state_trans.final_trans_state
        if (
            final_trans_state
            and str(final_trans_state.name).casefold() == "faulty"
            and not attrs.get("note")
        ):
            raise serializers.ValidationError(
                {"error": "you are required to add some notes for faulty rooms"}
            )
        return attrs

    def create(self, validated_data):
        user_profile = self.context.get("authored_by")
        if not helpers.check_profile_role(
            profile=user_profile, role_name="Supervisor"
        ) and helpers.check_profile_department(
            profile=user_profile, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {"error": "Only Supervisors for HouseKeeping department can complete this action"}
            )
        room_keeping_assign = validated_data.get("room_keeping_assign")
        shift = room_keeping_assign.shift
        room = room_keeping_assign.room
        instance = models.ProcessRoomKeeping.objects.create(
            room=room,
            room_keeping_assign=room_keeping_assign,
            room_state_trans=validated_data.get("room_state_trans"),
            date_processed=validated_data.get("date_processed"),
            shift=shift,
            created_by=user_profile,
        )
        return instance
