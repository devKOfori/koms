from rest_framework import serializers
from . import models
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from datetime import timedelta, date, datetime
from utils import generators, system_variables, notifications, helpers, choices


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
        with transaction.atomic():
            instance = models.RoomKeepingAssign.objects.create(
                **validated_data, created_by=created_by
            )

            # Create default processroomkeeping record
            default_trans_state = models.HouseKeepingStateTrans.objects.get(
                initial_trans_state__name__iexact="waiting",
                final_trans_state__name__iexact="assigned",
            )
            models.ProcessRoomKeeping.objects.create(
                room=instance.room,
                room_keeping_assign=instance,
                room_state_trans=default_trans_state,
                date_processed=instance.date_created,
                created_by=instance.created_by,
            )
        return instance

    def update(self, instance, validated_data):
        modified_by = self.context.get("modified_by")
        instance.room = validated_data.get("room", instance.room)
        instance.assignment_date = validated_data.get(
            "assignment_date", instance.assignment_date
        )
        instance.assigned_to = validated_data.get("assigned_to", instance.assigned_to)
        instance.last_modified_by = modified_by
        instance.save()
        return instance


class ProcessRoomKeepingSerializer(serializers.ModelSerializer):
    room_state_trans = serializers.SlugRelatedField(
        slug_field="name",
        queryset=models.HouseKeepingStateTrans.objects.all(),
    )
    shift = serializers.SlugRelatedField(slug_field="name", read_only=True)
    # shift = serializers.SlugRelatedField(
    #     slug_field="name", queryset=models.Shift.objects.all(), read_only=True
    # )
    room = serializers.SlugRelatedField(slug_field="room_number", read_only=True)
    # room = serializers.SlugRelatedField(
    #     slug_field="room_number", queryset=models.Room.objects.all(), read_only=True
    # )

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
        user_profile = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=user_profile,
            department_name=system_variables.DEPARTMENT_NAMES.get("house_keeping"),
        ):
            raise serializers.ValidationError(
                {
                    "error": "only staff of housekeeping department can complete this action"
                }
            )

        # faulty rooms requires that notes are added
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

        # only supervisors can set IP state
        # print(f'supervisor account? {helpers.check_profile_role(
        #         profile=user_profile,
        #         role_name=system_variables.ROLE_NAMES.get("supervisor"),
        #     )}')
        # print(f'User profile dept: {user_profile.roles.all()}')
        if (
            final_trans_state
            and str(final_trans_state.name).casefold() == "ip"
            and not helpers.check_profile_role(
                profile=user_profile,
                role_name=system_variables.ROLE_NAMES.get("supervisor"),
            )
        ):
            raise serializers.ValidationError(
                {"error": "only supervisors can set state to IP"}
            )

        # shift has not been assigned to you
        room_keeping_assign = attrs.get("room_keeping_assign")
        if user_profile != room_keeping_assign.assigned_to:
            # print(f'assigned_to and user_profile {attrs.get('assigned_to')}  {user_profile}')
            raise serializers.ValidationError(
                {"error": "Task has not been assigned to you"}
            )
        return attrs

    def create(self, validated_data):
        user_profile = self.context.get("authored_by")
        room_keeping_assign = validated_data.get("room_keeping_assign")
        shift = room_keeping_assign.shift
        room: models.Room = room_keeping_assign.room
        room_state_trans = validated_data.get("room_state_trans")
        with transaction.atomic():
            instance = models.ProcessRoomKeeping.objects.create(
                room=room,
                room_keeping_assign=room_keeping_assign,
                room_state_trans=room_state_trans,
                date_processed=validated_data.get("date_processed"),
                shift=shift,
                created_by=user_profile,
            )
            if room_state_trans.name == "cleaned-to-ip":
                # print(f'room status before {room.room_status}')
                # print('changing room status...')
                room.change_room_maintenance_status("cleaned")
                # print('room status changed...')
                room.save()
                # print(f'room status after {room.room_status}')
        return instance


class NameTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NameTitle
        fields = ["name"]


class ClientSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field="name", queryset=models.NameTitle.objects.all()
    )
    gender = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Gender.objects.all()
    )

    class Meta:
        model = models.Client
        fields = [
            "id",
            "title",
            "first_name",
            "last_name",
            "gender",
            "email",
            "phone_number",
            "address",
            "national_id",
        ]
        read_only_fields = ["id"]


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PaymentType
        fields = ["id", "name"]
        read_only_fields = ["id"]


class SponsorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SponsorType
        fields = ["id", "name", "allow_credit"]
        read_only_fields = ["id"]


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sponsor
        fields = ["id", "name", "email", "phone_number", "address", "fax"]
        read_only_fields = ["id"]


class BookingSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field="name", queryset=models.NameTitle.objects.all()
    )
    room = serializers.SlugRelatedField(
        slug_field="room_number", queryset=models.Room.objects.all()
    )
    receipt = serializers.SlugRelatedField(
        slug_field="receipt_number",
        queryset=models.Receipt.objects.all(),
        allow_null=True,
    )
    gender = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Gender.objects.all()
    )
    sponsor_type = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = models.Booking
        exclude = [
            "client",
            "room_category",
            "room_type",
            "room_number",
            "number_of_guests",
            "payment_type",
        ]
        read_only_fields = ["id"]

    def validate_room(self, room: models.Room):
        """
        Validate the room status for booking.

        Parameters:
        room: A Room instance.

        Raises:
        serializers.ValidationError: If the room's status is not 'cleaned'.

        Returns:
        the Room instance.

        """
        if room.room_maintenance_status != "cleaned":
            raise serializers.ValidationError(
                {
                    "error": "the room is not cleaned and is currently not available for booking"
                }
            )

        if room.room_booking_status == "booked":
            raise serializers.ValidationError(
                {"error": "the room currently has an active booking"}
            )

        return room

    def validate(self, attrs):
        check_in_date = attrs.get("check_in")
        check_out_date = attrs.get("check_out")

        # this condition prevents the creation of bookings where check-out date comes before check-in dates
        if check_in_date >= check_out_date:
            raise serializers.ValidationError(
                {"error": "Check-out date must be later than check-in date."}
            )

        room_max_guests = attrs.get("room").max_guests

        # this condition prevents the booking of rooms where the number of guests is greater than the room's max capacity
        if (
            attrs.get("number_of_older_guests", 0)
            + attrs.get("number_of_younger_guests", 0)
            > room_max_guests
        ):
            raise serializers.ValidationError(
                {"error": f"room takes a max of {room_max_guests} guests"}
            )

        sponsor = attrs.get("sponsor")
        receipt = attrs.get("receipt")
        # validations related to self-sponsoring bookings
        if sponsor and sponsor.sponsor_type.name.casefold() == "self":
            # this condition ensures that receipts are added to bookings that have 'self' as sponsor type
            if not receipt:
                raise serializers.ValidationError(
                    {"error": "Receipts are required for self-sponsored bookings."}
                )

            # this condition checks if the amount on a receipt can pay the cost of a booking
            if not receipt.can_pay(attrs.get("rate")):
                raise serializers.ValidationError(
                    {
                        "error": "the balance on the receipt cannot pay for the cost of the booking"
                    }
                )

        return attrs

    def create(self, validated_data: dict):
        # get user profile
        created_by = self.context["authored_by"]

        # this condition prevents all users who are not in frontdesk department from creating bookings
        if not helpers.check_profile_department(
            profile=created_by, department_name="frontdesk"
        ):
            raise serializers.ValidationError(
                {"error": "only frontdesk staff are authorized to complete this action"}
            )

        client_data = {}
        client_data_keys = [
            "title",
            "first_name",
            "last_name",
            "gender",
            "email",
            "phone_number",
            "address",
            "national_id",
            "emergency_contact_name",
            "emergency_contact_email",
        ]
        for attr, value in validated_data.items():
            if attr in client_data_keys:
                client_data[attr] = value

        with transaction.atomic():
            # Create client account
            client = models.Client.objects.create(**client_data)

            # Room-related data
            room: models.Room = validated_data.pop("room")
            room_type = room.room_type
            room_number = room.room_number

            # Sponsor and payment related data
            sponsor: models.Sponsor = validated_data.pop("sponsor")
            sponsor_type: models.SponsorType = sponsor.sponsor_type
            payment_type: models.PaymentType = (
                models.PaymentType.objects.get(name__iexact="self")
                if sponsor_type.name.casefold() == "self"
                else models.PaymentType.objects.get(name__iexact="credit")
            )

            # booking-related data
            number_of_guests = validated_data.get(
                "number_of_older_guests"
            ) + validated_data.get("number_of_older_guests")

            booking = models.Booking.objects.create(
                client=client,
                room=room,
                room_type=room_type,
                room_number=room_number,
                sponsor=sponsor,
                sponsor_type=sponsor_type,
                payment_type=payment_type,
                number_of_guests=number_of_guests,
                **validated_data,
            )

            # update 'room_booking_status' and 'room_maintenance_status'
            room.change_room_booking_status("booked")
            room.change_room_maintenance_status("used")
            room.save()

            # this condition, when true, updates the available amount field on a receipt
            if booking.payment_type.name.casefold() == "self" and booking.receipt:
                booking.receipt.pay(booking.rate)
                booking.receipt.save()

            return booking

    def update(self, instance, validated_data):
        # get user profile
        modified_by = self.context["authored_by"]
        client = instance.client

        # this condition prevents all users who are not in frontdesk department from updating bookings
        if not helpers.check_profile_department(
            profile=modified_by, department_name="frontdesk"
        ):
            raise serializers.ValidationError(
                {"error": "only frontdesk staff are authorized to complete this action"}
            )

        client_data = {}
        client_data_keys = [
            "title",
            "first_name",
            "last_name",
            "gender",
            "email",
            "phone_number",
            "address",
            "national_id",
            "emergency_contact_name",
            "emergency_contact_email",
        ]
        for attr, value in validated_data.items():
            if attr in client_data_keys:
                setattr(client, attr, value)
        with transaction.atomic():
            client.save()
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.client = client

            room: models.Room = validated_data.pop("room")
            room_type = room.room_type
            room_number = room.room_number

            # Sponsor and payment related data
            sponsor: models.Sponsor = validated_data.pop("sponsor")
            sponsor_type: models.SponsorType = sponsor.sponsor_type
            payment_type: models.PaymentType = (
                models.PaymentType.objects.get(name__iexact="self")
                if sponsor_type.name.casefold() == "self"
                else models.PaymentType.objects.get(name__iexact="credit")
            )

            # booking-related data
            number_of_guests = validated_data.get(
                "number_of_older_guests"
            ) + validated_data.get("number_of_older_guests")

            instance.room = room or instance.room
            instance.room_type = room_type or instance.room_type
            instance.room_number = room_number or instance.room_number
            instance.sponsor = sponsor or instance.sponsor
            instance.sponsor_type = sponsor_type or instance.sponsor_type
            instance.payment_type = payment_type or instance.payment_type
            instance.number_of_guests = number_of_guests or instance.number_of_guests
            instance.save()

            return instance


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Amenity
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        created_by = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=created_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        if not helpers.check_profile_role(profile=created_by, role_name="Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in house keeping are authorized to complete this action"
                }
            )
        return models.Amenity.objects.create(created_by=created_by, **validated_data)


class RoomCategorySerializer(serializers.ModelSerializer):
    amenities = serializers.SlugRelatedField(
        slug_field="name", many=True, queryset=models.Amenity.objects.all()
    )

    class Meta:
        model = models.RoomCategory
        fields = ["id", "name", "amenities"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        created_by = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=created_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        if not helpers.check_profile_role(profile=created_by, role_name="Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in house keeping are authorized to complete this action"
                }
            )
        amenities = validated_data.pop("amenities")
        room_category = models.RoomCategory.objects.create(
            created_by=created_by, **validated_data
        )
        room_category.amenities.set(amenities)
        return room_category

    def update(self, instance, validated_data):
        modified_by = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=modified_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        if not helpers.check_profile_role(profile=modified_by, role_name="Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in house keeping are authorized to complete this action"
                }
            )
        amenities = validated_data.pop("amenities")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.amenities.set(amenities)
        return instance


class RoomTypeSerializer(serializers.ModelSerializer):
    room_category = serializers.SlugRelatedField(
        slug_field="name", queryset=models.RoomCategory.objects.all()
    )
    amenities = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Amenity.objects.all(),
        allow_null=True,
    )
    view = serializers.SlugRelatedField(
        slug_field="name", queryset=models.HotelView.objects.all()
    )
    bed_types = serializers.SlugRelatedField(
        slug_field="name", queryset=models.BedType.objects.all(), many=True
    )

    class Meta:
        model = models.RoomType
        fields = [
            "id",
            "name",
            "amenities",
            "room_category",
            "area_in_meters",
            "area_in_feet",
            "bed_types",
            "rate",
            "view",
            "max_guests",
            "bed_types",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        created_by = self.context.get("authored_by")
        room_category = validated_data.get("room_category")
        if not helpers.check_profile_department(
            profile=created_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        amenities = validated_data.pop("amenities")
        bed_types = validated_data.pop("bed_types")
        if not amenities:
            amenities = room_category.amenities.all()

        room_type = models.RoomType.objects.create(
            created_by=created_by, **validated_data
        )
        room_type.amenities.set(amenities)
        room_type.bed_types.set(bed_types)
        return room_type

    def update(self, instance, validated_data):
        modified_by = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=modified_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        if not helpers.check_profile_role(profile=modified_by, role_name="Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in house keeping are authorized to complete this action"
                }
            )
        amenities = validated_data.pop("amenities")
        bed_types = validated_data.pop("bed_types")
        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        instance.save()
        # if there are no amenities provided, use the amenities from the room category
        instance.amenities.set(
            amenities or instance.room_category.amenities.all()
        )
        instance.bed_types.set(bed_types or instance.bed_types.all())
        return instance


class RoomSerializer(serializers.ModelSerializer):
    room_type = serializers.SlugRelatedField(
        slug_field="name", queryset=models.RoomType.objects.all()
    )
    floor = serializers.SlugRelatedField(
        slug_field="name", queryset=models.HotelFloor.objects.all()
    )
    room_category = serializers.SlugRelatedField(
        slug_field="name", queryset=models.RoomCategory.objects.all()
    )
    amenities = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Amenity.objects.all(),
        allow_null=True,
    )
    bed_type = serializers.SlugRelatedField(
        slug_field="name", queryset=models.BedType.objects.all(), allow_null=True
    )
    rate = serializers.DecimalField(allow_null=True, max_digits=10, decimal_places=2)

    class Meta:
        model = models.Room
        fields = [
            "id",
            "room_number",
            "room_type",
            "room_category",
            "max_guests",
            "rate",
            "floor",
            "room_maintenance_status",
            "room_booking_status",
            "amenities",
            "bed_type",
        ]
        read_only_fields = ["id", "room_maintenance_status", "room_booking_status"]

    def validate(self, attrs):
        if attrs.get("rate") and (attrs.get("rate") > attrs.get("room_type").rate):
            raise serializers.ValidationError(
                {"error": "The room's rate cannot be greater than the room type's rate"}
            )
        if attrs.get("max_guests") and (
            attrs.get("max_guests") > attrs.get("room_type").max_guests
        ):
            raise serializers.ValidationError(
                {
                    "error": "The room's max guests cannot be greater than the room type's max guests"
                }
            )
        return attrs

    def create(self, validated_data):
        created_by = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=created_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        if not helpers.check_profile_role(profile=created_by, role_name="Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in house keeping are authorized to complete this action"
                }
            )
        # get the rate and max_guests from the room type if not provided
        rate = validated_data.pop("rate", 0)
        max_guests = validated_data.pop("max_guests", 0)
        if not rate:
            rate = validated_data.get("room_type").rate
        if not max_guests:
            max_guests = validated_data.get("room_type").max_guests

        # get the amenities from the room type if not provided
        amenities = validated_data.pop("amenities")
        if not amenities:
            amenities = validated_data.get("room_type").amenities.all()

        room = models.Room.objects.create(
            created_by=created_by,
            **validated_data,
            rate=rate,
            max_guests=max_guests,
            room_maintenance_status="used",
            room_booking_status="unavailable",
            is_occupied=False,
        )
        room.amenities.set(amenities)
        return room

    def update(self, instance, validated_data):
        modified_by = self.context.get("authored_by")
        if not helpers.check_profile_department(
            profile=modified_by, department_name="house keeping"
        ):
            raise serializers.ValidationError(
                {
                    "error": "only house keeping staff are authorized to complete this action"
                }
            )
        if not helpers.check_profile_role(profile=modified_by, role_name="Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in house keeping are authorized to complete this action"
                }
            )

        rate = validated_data.pop("rate", 0)
        max_guests = validated_data.pop("max_guests", 0)
        if not rate:
            rate = validated_data.get("room_type").rate
        if not max_guests:
            max_guests = validated_data.get("room_type").max_guests

        # get the amenities from the room type if not provided
        amenities = validated_data.pop("amenities")
        if not amenities:
            amenities = validated_data.get("room_type").amenities.all()

        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)

        instance.rate = rate
        instance.max_guests = max_guests
        instance.amenities.set(amenities)

        instance.save()

        return instance


class ComplaintSerializer(serializers.ModelSerializer):
    complaint_items = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Amenity.objects.all(),
        allow_null=True,
    )
    title = serializers.CharField(max_length=255, allow_null=True)
    room_number = serializers.SlugRelatedField(slug_field="room_number", queryset=models.Room.objects.all())

    class Meta:
        model = models.Complaint
        fields = [
            "id",
            "client",
            "room_number",
            "title",
            "message",
            "date_created",
            "complaint_items",
            "department",
            "priority",
            "status",
            "date_resolved",
            "resolved_by",
            "hashtags",
        ]
        read_only_fields = [
            "id",
            "date_created",
            "created_by",
            "status",
            "date_resolved",
            "resolved_by",
            "hashtags",
            "department",
            "priority",
        ]
