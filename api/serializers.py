from rest_framework import serializers
from . import models
from rest_framework import status
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from datetime import timedelta, date, datetime
from utils import generators, system_variables, notifications, helpers, choices
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenBlacklistSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    this class customize the token claims
    by adding the user roles and the user department
    """

    def validate(self, attrs):
        print(f"{self}...")
        data = super().validate(attrs=attrs)
        user = self.user
        refresh = self.get_token(user=user)
        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        if hasattr(user, "profile"):

            username = getattr(user, "username", "No Username")
            user_id = getattr(user, "id", "No ID")
            profile = getattr(user, "profile", "No Profile")
            # print(profile)
            data["username"] = username
            data["user_id"] = user_id
            data["profile_id"] = profile.id

            department_name = (
                getattr(user.profile.department, "name", "unknown")
            )
            data["department"] = department_name
            if hasattr(user.profile, "roles"):
                roles = [role.role.name for role in user.profile.roles.all()]
                data["roles"] = roles
            else:
                data[roles] = []

        return data

class CustomTokenBlacklistSerializer(TokenBlacklistSerializer):
    def validate(self, attrs):
        print(attrs)
        data = super().validate(attrs=attrs)

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True)
    class Meta:
        model = models.CustomUser
        fields = ["id", "username", "first_name", "last_name", "password"]
        read_only_fields = ["id"]
        
class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Gender
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        created_by = self.context.get("created_by")
        gender = models.Gender.objects.create(**validated_data, 
                                              created_by=created_by)
        return gender

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = ["id", "name", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

    def create(self, validated_data):
        with transaction.atomic():
            created_by = self.context.get("created_by")
            date_created = timezone.now()
            department = models.Department.objects.create(**validated_data, 
                                                          created_by=created_by, 
                                                          date_created=date_created)
            
            # create corresponding group
            Group.objects.get_or_create(name=validated_data.get("name"))
        return department

    def update(self, instance, validated_data):
        with transaction.atomic():
            old_name = instance.name
            new_name = validated_data.get("name", old_name)
            instance.name = new_name
            instance.description = validated_data.get("description", instance.description)
            instance.save()
            if old_name != new_name:
                try:
                    group = Group.objects.get(name=old_name)
                    group.name = new_name
                    group.save()
                except Group.DoesNotExist:
                    Group.objects.create(name=new_name)
        return instance

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Role
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        with transaction.atomic():
            role = models.Role.objects.create(**validated_data)
            Group.objects.get_or_create(name=validated_data.get("name"))
        return role

    def update(self, instance: models.Role, validated_data)->models.Role:
        with transaction.atomic():
            old_name = instance.name
            new_name = validated_data.get("name", old_name)
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

    def create(self, validated_data):
        created_by = self.context["created_by"]
        print(f"ProfileRolesSerializer: {self.context}")
        profile = models.Profile.objects.get(id=self.context["profile_id"])
        profile_role = models.ProfileRole.objects.create(
            profile=profile,
            created_by=created_by,
            **validated_data
        )
        group_name = validated_data.get("role").name
        group, created = Group.objects.get_or_create(name=group_name)
        profile.user.groups.add(group)
        return profile_role

class CustomUserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    department = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Department.objects.all()
    )
    gender = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Gender.objects.all()
    )

    class Meta:
        model = models.Profile
        fields = [
            "id",
            "user",
            "gender",
            "birthdate",
            "phone_number",
            "email",
            "residential_address",
            "photo",
            "full_name",
            "department",
        ]
        read_only_fields = ["id", "full_name"]
    
    def create(self, validated_data):
        print(validated_data)
        created_by: models.Profile = self.context.get("created_by")
        user_data = validated_data.pop("user")


        with transaction.atomic():
            user: models.CustomUser = models.CustomUser.objects.create_user(
                username=user_data.get("username"),
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                password=user_data.get("password"),
            )
            user_profile = models.Profile.objects.create(
                **validated_data,
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                created_by=created_by
            )
        return user_profile
      
class ProfileViewSerializer(serializers.Serializer):
    user = CustomUserSerializer()
    roles = ProfileRolesSerializer(many=True)  

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

    def create(self, validated_data):
        username: str = validated_data.get("username")
        reset_channel: str = validated_data.get("reset_channel")
        reset_channel = reset_channel.casefold()
        reset_token, reset_code = None, None
        try:
            user_profile = models.Profile.objects.select_related("user").get(user__username=username)    
            if reset_channel=="email":
                if not user_profile.email:
                    raise serializers.ValidationError(
                        {"error": "The user does not have an email address set."},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
                else: 
                    reset_token = generators.generate_password_reset_token()
            if reset_channel=="sms":
                if not user_profile.phone_number:
                    raise serializers.ValidationError(
                        {"error": "The user does not have a phone number set."},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    reset_code = generators.generate_password_reset_code()
                    print(f"reset_code: {reset_code}")
            print(f"reset_token: {reset_token}")
            instance = models.PasswordReset.objects.create(
                username=username,
                user=user_profile.user,
                reset_token=reset_token,
                reset_channel=reset_channel,
                reset_code=reset_code,
                expiry_date=timezone.now() + timedelta(days=system_variables.PASSWORD_RESET.get("RESET_EXPIRY_DURATION", 2)),
                is_used=False
            )
            return instance
        except models.Profile.DoesNotExist:
            raise serializers.ValidationError(
                {"error": f"Profile with username '{username}' does not exist."},
                code=status.HTTP_400_BAD_REQUEST,
            )

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Shift
        fields = ["id", "name", "start_time", "end_time"]
        read_only_fields = ["id"]

class ProfileShiftAssignSerializer(serializers.ModelSerializer):
    # profile = CustomUserProfileSerializer()
    status = serializers.SlugRelatedField(
        slug_field="name", queryset=models.ShiftStatus.objects.all()
    )
    employee_name = serializers.SerializerMethodField(read_only=True)
    shift_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.ProfileShiftAssign
        fields = [
            "id",
            "profile",
            "shift",
            "date",
            "shift_start_time",
            "shift_end_time",
            "employee_name",
            "status",
            "shift_name",
        ]
        read_only_fields = ["id", "shift_start_time" "shift_end_time"]

    def get_employee_name(self, obj):
        return obj.profile.full_name if obj.profile else None

    def get_shift_name(self, obj):
        return obj.shift.name if obj.shift else None

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
        shift_start_time = datetime.combine(
            validated_data.get("date"), validated_data.get("shift").start_time
        )
        shift_end_time = datetime.combine(
            validated_data.get("date"), validated_data.get("shift").end_time
        )
        print(f"shift_end_time: {shift_end_time}")
        created_by = self.context.get("created_by")
        department = created_by.department
        return models.ProfileShiftAssign.objects.create(
            department=department,
            created_by=created_by,
            shift_start_time=shift_start_time,
            shift_end_time=shift_end_time,
            **validated_data,
        )

    def update(self, instance, validated_data):
        modified_by = self.context.get("modified_by")
        for attr, value in validated_data.items():
            if hasattr(instance, attr):
                setattr(instance, attr, value)
        instance.modified_by = modified_by
        instance.save()
        return instance

class MyShiftSerializer(serializers.ModelSerializer):
    shift = serializers.SlugRelatedField(slug_field="name", read_only=True)
    start_time = serializers.SerializerMethodField(read_only=True)
    end_time = serializers.SerializerMethodField(read_only=True)
    status = serializers.SlugRelatedField(slug_field="name", read_only=True)

    class Meta:
        model = models.ProfileShiftAssign
        fields = [
            "id",
            "shift",
            "date",
            "status",
            "start_time",
            "end_time",
            "shift_end_time",
        ]
        read_only_fields = ["id"]

    def get_start_time(self, obj):
        return obj.shift.start_time if obj.shift else None

    def get_end_time(self, obj):
        return obj.shift.end_time if obj.shift else None

class ShiftStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShiftStatus
        fields = ["id", "name"]
        read_only_fields = ["id"]

class ShiftAssignmentSerializer(serializers.ModelSerializer):
    profile = serializers.SlugRelatedField(slug_field="full_name", read_only=True)

    class Meta:
        model = models.ProfileShiftAssign
        fields = ["id", "profile", "shift", "date", "username"]
        read_only_fields = ["id"]

class ShiftNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShiftNote
        fields = ["id", "note", "assigned_shift", "note_date"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        assigned_shift = attrs.get("assigned_shift")
        created_by = self.context.get("created_by")
        last_modified_by = self.context.get("last_modified_by")
        if (
            assigned_shift.profile != created_by
            and assigned_shift.profile != last_modified_by
        ):
            raise serializers.ValidationError(
                {"error": "You can only add notes to shifts assigned to you"}
            )

        return attrs

    def create(self, validated_data):
        created_by = self.context.get("created_by")
        last_modified_by = self.context.get("last_modified_by")
        assigned_shift = validated_data.get("assigned_shift")
        note = validated_data.get("note")
        note_date = validated_data.get("note_date")
        shift_note = models.ShiftNote.objects.create(
            assigned_shift=assigned_shift,
            note=note,
            note_date=note_date,
            created_by=created_by,
            last_modified_by=last_modified_by,
        )
        return shift_note

    def update(self, instance, validated_data):
        last_modified_by = self.context.get("last_modified_by")
        instance.note = validated_data.get("note", instance.note)
        instance.note_date = validated_data.get("note_date", instance.note_date)
        instance.last_modified_by = last_modified_by
        instance.save()
        return instance

class RoomKeepingAssignSerializer(serializers.ModelSerializer):
    room = serializers.SlugRelatedField(
        slug_field="room_number", queryset=models.Room.objects.all()
    )
    shift = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Shift.objects.all()
    )
    priority = serializers.SlugRelatedField(
        slug_field="name",
        queryset=models.Priority.objects.all(),
        allow_null=True,
        required=False,
    )
    status = serializers.SerializerMethodField(read_only=True)
    status_2 = serializers.BooleanField(write_only=True)
    created_by = serializers.SlugRelatedField(slug_field="full_name", read_only=True)
    task_supported = serializers.CharField(
        max_length=255, required=False, write_only=True
    )
    profile_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.RoomKeepingAssign
        fields = [
            "id",
            "room",
            "shift",
            "member_shift",
            "assignment_date",
            "assigned_to",
            "title",
            "description",
            "priority",
            "status",
            "status_2",
            "created_by",
            "current_status",
            "task_supported",
            "profile_name",
        ]
        read_only_fields = ["id", "created_by", "member_shift", "current_status"]

    def get_status(self, obj):
        return obj.room_keeping_status_processes.first().status.name

    def get_profile_name(self, obj):
        return obj.assigned_to.full_name if obj.assigned_to else None

    def validate_assignment_date(self, data):
        if data < date.today():
            raise serializers.ValidationError(
                {"error": "Room Keeping Assignments cannot be saved for past dates"}
            )
        return data

    def create(self, validated_data):
        print(validated_data)
        is_new_record = validated_data.pop("status_2", None)
        task_supported = validated_data.pop("task_supported", None)
        record_status = None
        if is_new_record is not None:
            record_status = "Pending" if is_new_record else "Reassigned"
        created_by = self.context.get("created_by")
        shift = validated_data.get("shift")
        assignment_date = validated_data.get("assignment_date")
        profile = validated_data.get("assigned_to")
        # if not helpers.check_profile_department(created_by, "Housekeeping"):
        if not created_by.is_member_of("Housekeeping"):
            raise serializers.ValidationError(
                {"error": "User must be in house keeping to complete this action"},
                code=status.HTTP_400_BAD_REQUEST,
            )
        # if not helpers.check_profile_role(created_by, "Supervisor"):
        if not created_by.has_role("Supervisor"):
            raise serializers.ValidationError(
                {"error": "Only supervisors of housekeeping can complete this action"},
                code=status.HTTP_400_BAD_REQUEST,
            )
        # if not helpers.check_user_shift(
        #     date=assignment_date,
        #     profile=profile,
        #     shift_name=shift.name,
        # ):
        if not profile.has_shift(assignment_date, shift.name):
            raise serializers.ValidationError(
                {"error": f"The user has no {shift.name} on {assignment_date}"}
            )
        with transaction.atomic():
            if task_supported:
                task_supported_obj = models.RoomKeepingAssign.objects.get(
                    id=task_supported
                )
                task_supported_obj.change_status(
                    "Support Assigned", created_by=created_by
                )
                task_supported_obj.save()

            member_shift = created_by.shifts.get(date=assignment_date, shift=shift)
            instance = models.RoomKeepingAssign.objects.create(
                **validated_data,
                created_by=created_by,
                member_shift=member_shift,
                task_supported=task_supported,
            )

            instance.change_status("Pending", created_by=created_by)
            instance.save()
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

class NameTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NameTitle
        fields = ["id", "name", "description", "created_by", "date_created"] 
        read_only_fields = ["id", "created_by", "date_created"]

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

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Country
        fields = ["id", "name", "country_code", "abbr", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]
  
class GuestSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        slug_field="name", queryset=models.NameTitle.objects.all()
    )
    gender = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Gender.objects.all()
    )
    identification_type = serializers.SlugRelatedField(
        slug_field="name", queryset=models.IdentificationType.objects.all()
    )
    country = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Country.objects.all()
    )

    class Meta:
        model = models.Guest
        fields = [
            "id",
            "guest_id",
            "title",
            "first_name",
            "last_name",
            "gender",
            "email",
            "phone_number",
            "address",
            "identification_type",
            "identification_number",
            "country",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]
        read_only_fields = ["id", "guest_id"]

    def create(self, validated_data):
        guest_id = generators.generate_guest_id()
        first_name = validated_data["first_name"]
        last_name = validated_data["last_name"]
        with transaction.atomic():
            guest_user = get_user_model().objects.create_user(
                username=f"{first_name.lower()}.{last_name.lower()}",
                first_name=first_name,
                last_name=last_name,
                password=f"{first_name.lower()}.{last_name.lower()}{guest_id[-4:]}", 
                is_staff=False,
                is_active=False,
                email=validated_data.get("email", ""),
                user_category="guest",
            )
            guest = models.Guest.objects.create(
                **validated_data,
                guest_id=guest_id,
                user=guest_user,
            )
            return guest

class BookingSerializer(serializers.ModelSerializer):
    guest = GuestSerializer(write_only=True)
    payment_status = serializers.SlugRelatedField(
        slug_field="name", read_only=True)
    # room_category = serializers.SlugRelatedField(
    #     slug_field="name", queryset=models.RoomCategory.objects.all(), required=False
    # )
    room_type = serializers.SlugRelatedField(
        slug_field="name", queryset=models.RoomType.objects.all()
    )
    number_of_younger_guests = serializers.IntegerField(required=False)
    number_of_guests = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.Booking
        fields = [
            "id",
            "guest",
            "guest_id",
            "guest_name",
            "email",
            "phone_number",
            # "room_category",
            "room_type",
            "room_number",
            "booking_code",
            "check_in_date",
            "check_out_date",
            "number_of_older_guests",
            "number_of_younger_guests",
            "number_of_guests",
            "rate",
            "amount_paid",
            "promo_code",
            "vip_status",
            # "sponsor",
            "payment_status",
            "note",
            "date_created",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "guest_id",
            "room_number",
            "booking_code",
            "guest_name",
            "email",
            "room_category",
            "phone_number",
            "created_by",
            "rate",
            "vip_status",
            "number_of_guests",
            "payment_status",
            "created_by",
        ]

    def validate_check_in_date(self, data):
        if data.date() < timezone.now().date():
            raise serializers.ValidationError(
                {"error": "Check-in date cannot be in the past"}
            )
        return data

    def validate_check_out_date(self, data):
        if data.date() < timezone.now().date():
            raise serializers.ValidationError(
                {"error": "Check-out date cannot be in the past"}
            )
        return data

    def validate(self, attrs):
        check_in_date = attrs.get("check_in_date")
        check_out_date = attrs.get("check_out_date")
        if check_in_date >= check_out_date:
            raise serializers.ValidationError(
                {"error": "Check-out date must be later than check-in date"}
            )
        return attrs

    def create(self, validated_data):
        creator = self.context.get("authored_by")
        guest_data = validated_data.pop("guest")
        print(guest_data)
        with transaction.atomic():
            guest = models.Guest.objects.create(guest_id=generators.generate_guest_id(), **guest_data)
            booking = models.Booking.objects.create(
                guest=guest,
                guest_name=f"{guest.first_name} {guest.last_name}",
                booking_code=generators.generate_booking_code(),
                email=guest.email,
                phone_number=guest.phone_number,
                room_category=validated_data.get("room_type").room_category,
                number_of_guests=validated_data.get("number_of_older_guests", 0)
                + validated_data.get("number_of_younger_guests", 0),
                created_by=creator,
                **validated_data,
            )
            return booking
        
class IdentificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IdentificationType
        fields = ["id", "name", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

class CheckInSerializer(serializers.ModelSerializer):
    # guest = serializers.SlugRelatedField(
    #     slug_field="guest_id", queryset=models.Guest.objects.all(), required=False, allow_null=True
    # )
    class Meta:
        model = models.Checkin
        fields = [
            "id",
            # "booking_code",
            # "guest",
            "guest_id",
            "guest_name",
            "gender",
            "email",
            "phone_number",
            "room",
            "room_type",
            "check_in_date",
            "number_of_older_guests",
            "number_of_younger_guests",
            "number_of_guests",
            "sponsor",
            "total_payment",
            "check_out_date",
            "checked_out",
        ]
        read_only_fields = [
            "id",
            "checked_out",
            "number_of_guests",
        ]

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Amenity
        fields = ["id", "name", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

class RoomCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RoomCategory
        fields = ["id", "name", "room_area", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

class BedTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BedType
        fields = ["id", "name", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

class RoomTypeSerializer(serializers.ModelSerializer):
    amenities = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Amenity.objects.all(),
        required=False,
    )

    class Meta:
        model = models.RoomType
        fields = [
            "id",
            "name",
            "max_occupancy",
            "base_price",
            "amenities",
            "created_by",
            "date_created",
        ]
        read_only_fields = ["id", "created_by", "date_created"]

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HotelFloor
        fields = ["id", "name", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

class HotelViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HotelView
        fields = ["id", "name", "description", "created_by", "date_created"]
        read_only_fields = ["id", "created_by", "date_created"]

class RoomSerializer(serializers.ModelSerializer):
    room_type = serializers.SlugRelatedField(
        slug_field="name", queryset=models.RoomType.objects.all()
    )
    floor = serializers.SlugRelatedField(
        slug_field="name", queryset=models.HotelFloor.objects.all(), required=False
    )
    room_category = serializers.SlugRelatedField(
        slug_field="name", queryset=models.RoomCategory.objects.all(), required=False
    )
    amenities = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Amenity.objects.all(),
        required=False,
    )
    bed_type = serializers.SlugRelatedField(
        slug_field="name", queryset=models.BedType.objects.all(), required=False
    )

    class Meta:
        model = models.Room
        fields = [
            "id",
            "room_number",
            "floor",
            "room_type",
            "room_category",
            "room_area",
            "room_view",
            "max_occupancy",
            "bed_type",
            "is_occupied",
            "is_available",
            "is_cleaned",
            "room_maintenance_status",
            "room_booking_status",
            "amenities",
            "current_guest",
            "current_price",
            "date_created",
            "created_by",
        ]
        read_only_fields = ["id", "room_maintenance_status", "room_booking_status", "date_created", "created_by", "is_occupied", "is_available", "is_cleaned", "current_guest", "current_price", "room_area", "max_occupancy", "last_price_update"]

    def create(self, validated_data):
        room_type: models.RoomType = validated_data.get("room_type")
        room_category: models.RoomCategory = validated_data.get("room_category")
        room_area = 0
        if room_category:
            room_area = getattr(room_category, "room_area", 0)
        max_occupancy = getattr(room_type, "max_occupancy", 1)
        amenities = validated_data.pop("amenities", None)
        if amenities is None:
            amenities = room_type.amenities.all()
        today = timezone.now().date()
        rate_obj = (
            room_type.room_rates
            .filter(
                start_date__lte=today, end_date__gte=today
            )
            .order_by("-start_date")
            .first()
        )
        current_price = getattr(rate_obj, "price", room_type.base_price)
        room = models.Room.objects.create(
            **validated_data,
            room_area=room_area,
            max_occupancy=max_occupancy,
            current_price=current_price,
        )
        room.amenities.set(amenities)
        return room


    def update(self, instance, validated_data):
        room_type = validated_data.get("room_type")
        room_category = validated_data.get("room_category")
        instance.room_number = validated_data.get(
            "room_number", instance.room_number
        )
        amenities = validated_data.pop("amenities", None)
        instance.room_type = room_type
        instance.max_occupancy = getattr(room_type, "max_occupancy", instance.max_occupancy)
        if room_category:
            instance.room_category = room_category
            instance.room_area = getattr(room_category, "room_area", instance.room_area)
        if amenities is None:
            instance.amenities.set(room_type.amenities.all())
        else:
            instance.amenities.set(amenities)
        instance.floor = validated_data.get("floor", instance.floor)
        instance.room_view = validated_data.get("room_view", instance.room_view)
        instance.bed_type = validated_data.get("bed_type", instance.bed_type)
        instance.save()
        return instance
    
class AssignComplaintSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=models.Profile.objects.all(), allow_null=True
    )
    assigned_to_department = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Department.objects.all(), allow_null=True
    )
    # complaint = serializers.PrimaryKeyRelatedField(queryset=models.Complaint.objects.all())
    priority = serializers.SlugRelatedField(
        slug_field="name", queryset=models.Priority.objects.all(), allow_null=True
    )
    hashtags = serializers.SlugRelatedField(
        slug_field="name",
        queryset=models.Hashtag.objects.all(),
        many=True,
        allow_null=True,
    )
    assigned_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.AssignComplaint
        fields = [
            "id",
            "complaint",
            "assigned_to",
            "assigned_to_department",
            "date_assigned",
            "assigned_by",
            "priority",
            "hashtags",
            "created_on",
        ]
        read_only_fields = ["id", "created_on", "assigned_by"]

    def validate(self, attrs):
        created_by = self.context.get("authored_by")
        # if not helpers.check_profile_department(
        #     profile=created_by, department_name="frontdesk"
        # ):
        if not created_by.is_member_of("Frontdesk"):
            raise serializers.ValidationError(
                {"error": "only frontdesk staff are authorized to complete this action"}
            )
        # if not helpers.check_profile_role(profile=created_by, role_name="Supervisor"):
        if not created_by.has_role("Supervisor"):
            raise serializers.ValidationError(
                {
                    "error": "only supervisors in frontdesk are authorized to complete this action"
                }
            )

        assigned_to = attrs.get("assigned_to")
        assigned_to_department = attrs.get("assigned_to_department")
        # check if the complaint is being assigned to a staff or a department
        if not assigned_to and not assigned_to_department:
            raise serializers.ValidationError(
                {
                    "error": "you must provide either a staff or a department to assign the complaint to"
                }
            )
        return attrs

    def create(self, validated_data):
        assigned_by = self.context.get("authored_by")
        complaint = validated_data.get("complaint")
        title = complaint.title
        message = complaint.message
        hashtags = validated_data.pop("hashtags")
        with transaction.atomic():
            instance = models.AssignComplaint.objects.create(
                title=title, message=message, **validated_data, assigned_by=assigned_by
            )
            instance.hashtags.set(hashtags)
            # change the status of the complaint to assigned
            complaint_status_assigned, _ = models.ComplaintStatus.objects.get_or_create(
                name="assigned"
            )
            complaint.complaint_status = complaint_status_assigned
            complaint.save()
        return instance

    def update(self, instance, validated_data):
        hashtags = validated_data.pop("hashtags")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        instance.hashtags.set(hashtags)
        return instance

class ProcessComplaintSerializer(serializers.ModelSerializer):
    complaint_status = serializers.SlugRelatedField(
        slug_field="name", queryset=models.ComplaintStatus.objects.all()
    )
    complaint = serializers.PrimaryKeyRelatedField(
        queryset=models.Complaint.objects.all(), allow_null=True
    )
    assigned_complaint = serializers.PrimaryKeyRelatedField(
        queryset=models.AssignComplaint.objects.all(), allow_null=True
    )

    class Meta:
        model = models.ProcessComplaint
        fields = [
            "id",
            "complaint",
            "assigned_complaint",
            "process_complaint_date",
            "note",
            "complaint_status",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        processed_by = self.context.get("authored_by")
        complaint = validated_data.get("complaint")
        assigned_complaint = validated_data.get("assigned_complaint")
        complaint_status = validated_data.get("complaint_status")
        complaint_updated_on = validated_data.get("created_on")
        with transaction.atomic():
            if not complaint and not assigned_complaint:
                raise serializers.ValidationError(
                    {
                        "error": "you must provide either a complaint or an assigned complaint"
                    }
                )
            instance = models.ProcessComplaint.objects.create(
                **validated_data, processed_by=processed_by
            )
            # change the status of the complaint to resolved
            if complaint:
                complaint.status = complaint_status
                complaint.updated_on = complaint_updated_on
                complaint.updated_by = processed_by
                complaint.save()

            if assigned_complaint:
                # check if the user is authorized to process the complaint
                if (
                    assigned_complaint.assigned_to
                    and not assigned_complaint.assigned_to == processed_by
                ):
                    raise serializers.ValidationError(
                        {"error": "you are not authorized to process this complaint"}
                    )
                if (assigned_complaint.assigned_to_department) and (
                    assigned_complaint.assigned_to_department != processed_by.department
                ):
                    raise serializers.ValidationError(
                        {"error": "you are not authorized to process this complaint"}
                    )
                assigned_complaint.status = complaint_status
                assigned_complaint.updated_on = complaint_updated_on
                assigned_complaint.save()
        return instance

    def update(self, instance, validated_data):
        processed_by = self.context.get("authored_by")
        if instance.processed_by != processed_by:
            raise serializers.ValidationError(
                {"error": "you are not authorized to update this record"}
            )
        if instance.processed_by.department != processed_by.department:
            raise serializers.ValidationError(
                {"error": "you are not authorized to update this record"}
            )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ComplaintSerializer(serializers.ModelSerializer):
    complaint_items = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Amenity.objects.all(),
        allow_null=True,
    )
    title = serializers.CharField(max_length=255, allow_null=True, allow_blank=True)
    room_number = serializers.SlugRelatedField(
        slug_field="room_number", queryset=models.Room.objects.all()
    )
    assigned_complaints = AssignComplaintSerializer(many=True, read_only=True)
    process_complaints = ProcessComplaintSerializer(many=True, read_only=True)

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
            "updated_on",
            "updated_by",
            "hashtags",
            "assigned_complaints",
            "process_complaints",
        ]
        read_only_fields = [
            "id",
            "date_created",
            "created_by",
            "status",
            "updated_on",
            "updated_by",
            "hashtags",
            "department",
            "priority",
            "assigned_complaints",
            "process_complaints",
        ]

class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Priority
        fields = ["id", "name"]
        read_only_fields = ["id"]
