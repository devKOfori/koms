import os
from typing import Literal, Optional
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from utils import defaults, choices
import uuid, datetime
from . import managers
from django.conf import settings
from utils.system_variables import PASSWORD_RESET
from rest_framework import serializers
from django.db import transaction

# Create your models here.


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    
    class Meta:
        abstract = True

class Department(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    class Meta(BaseModel.Meta):
        db_table = "department"

class CustomUser(AbstractBaseUser, BaseModel, PermissionsMixin):
    username = models.CharField(unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = managers.CustomUserManager()

    class Meta(BaseModel.Meta):
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"

class PasswordReset(BaseModel):
    username = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    reset_channel = models.CharField(
        max_length=30, choices=choices.PASSWORD_RESET_CHANNEL_CHOICES
    )
    expiry_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.token

    class Meta(BaseModel.Meta):
        db_table = "passwordreset"
        verbose_name = "Password Reset"
        verbose_name_plural = "Password Resets"

    @property
    def is_token_expired(self):
        time_diff = self.expiry_date - self.date_created
        return time_diff.total_seconds() / 3600 > PASSWORD_RESET.get(
            "RESET_TOKEN_EXPIRY_DURATION"
        )

def profile_photo_upload_path(instance, filename: str):
    ext = os.path.splitext(filename)[1]
    return f"profile_photos/{instance.user.id}{ext}"

class Gender(BaseModel):
    name = models.CharField(max_length=10)
    created_by = models.ForeignKey(
        "Profile", on_delete=models.SET_NULL, null=True, related_name="genders_created"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "gender"

class Profile(BaseModel):
    full_name = models.CharField(max_length=255)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name="profiles"
    )
    profile_roles = models.ManyToManyField(
        "Role", through="ProfileRole", through_fields=("profile", "role")
    )
    birthdate = models.DateField(null=True)
    photo = models.ImageField(upload_to=profile_photo_upload_path, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    residential_address = models.CharField(max_length=255, blank=True, null=True)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="profiles_created"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    def is_member_of(self, department_name: str) -> bool:
        return self.department.name == department_name

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(role__name__iexact=role_name, is_active=True).exists()

    def has_shift(self, date, shift_name: str) -> bool:
        return self.shifts.filter(date=date, shift__name__iexact=shift_name).exists()

    class Meta(BaseModel.Meta):
        db_table = "profile"

class Role(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    class Meta(BaseModel.Meta):
        db_table = "role"

class ProfileRole(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="profiles")
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.profile.full_name} - [{self.role.name}]"

    class Meta(BaseModel.Meta):
        db_table = "profilerole"
        verbose_name = "Profile Role"
        verbose_name_plural = "Profile Roles"

class Shift(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "workshift"

class ShiftStatus(BaseModel):
    name = models.CharField(max_length=255)
    change_after_expiry = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "shiftstatus"

class ProfileShiftAssign(BaseModel):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="shifts"
    )
    date = models.DateField(default=timezone.now)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    shift_start_time = models.DateTimeField(null=True, blank=True)
    shift_end_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name="created_shifts"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name="modified_shifts"
    )
    date_modified = models.DateTimeField(auto_now=True)
    status = models.ForeignKey(ShiftStatus, on_delete=models.SET_NULL, null=True)
    time_started = models.DateTimeField(null=True, blank=True)
    time_ended = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{datetime.datetime.strftime(self.date, '%a %d %b %Y')} - {self.profile} - {self.shift}"

    @property
    def is_ended(self):
        return self.shift_end_time >= timezone.now()

    def change_status(self, new_status):
        self.status = ShiftStatus.objects.get(name=new_status)

    class Meta(BaseModel.Meta):
        db_table = "profileshiftassign"
        verbose_name = "Shift Assignment"
        verbose_name_plural = "Shift Assignments"
        ordering = ["-date"]

class ShiftNote(BaseModel):
    assigned_shift = models.OneToOneField(
        ProfileShiftAssign, on_delete=models.CASCADE, related_name="shift_notes"
    )
    note = models.TextField()
    note_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_shift_notes",
    )
    last_modified_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_shift_notes",
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.assigned_shift} - {self.date_created}"

    class Meta(BaseModel.Meta):
        db_table = "shiftnote"
        verbose_name = "Shift Note"
        verbose_name_plural = "Shift Notes"

class HotelFloor(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "hotelfloor"

class HotelView(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "hotelview"
        verbose_name = "Hotel View"
        verbose_name_plural = "Hotel Views"

class Amenity(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "amenities"
        verbose_name = "Amenity"
        verbose_name_plural = "Amenities"

class BedType(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "bedtype"
        verbose_name = "Bed Type"
        verbose_name_plural = "Beds Types"

class RoomCategory(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    amenities = models.ManyToManyField(Amenity)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "roomcategory"
        verbose_name = "Room Category"
        verbose_name_plural = "Room Categories"

class RoomType(BaseModel):
    name = models.CharField(max_length=255)
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True, related_name="room_types"
    )
    area_in_meters = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    area_in_feet = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    max_guests = models.IntegerField(default=1)
    bed_types = models.ManyToManyField(BedType)
    view = models.ForeignKey(HotelView, on_delete=models.SET_NULL, null=True)
    amenities = models.ManyToManyField(Amenity)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "roomtype"
        verbose_name = "Room Type"
        verbose_name_plural = "Room Types"

class Room(BaseModel):
    room_number = models.CharField(max_length=255, db_index=True)
    floor = models.ForeignKey(HotelFloor, on_delete=models.SET_NULL, null=True)
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True
    )
    room_type = models.ForeignKey(
        RoomType, on_delete=models.SET_NULL, null=True, related_name="rooms"
    )
    bed_type = models.ForeignKey(
        BedType, on_delete=models.SET_NULL, null=True, related_name="rooms"
    )
    rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    max_guests = models.PositiveIntegerField(default=1, null=True)
    is_occupied = models.BooleanField(default=False)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    # room_status = models.ForeignKey(
    #     "RoomStatus",
    #     on_delete=models.SET_DEFAULT,
    #     default=ROOM_STATUS_DEFAULT,
    # )
    room_maintenance_status = models.CharField(
        max_length=255,
        choices=choices.ROOM_MAINTENANCE_STATUS_CHOICES,
        default="default",
    )
    room_booking_status = models.CharField(
        max_length=255, choices=choices.ROOM_BOOKING_STATUS_CHOICES, default="default"
    )
    amenities = models.ManyToManyField(Amenity, related_name="rooms")

    def __str__(self):
        return self.room_number

    def change_room_maintenance_status(
        self, status: Literal["cleaned", "used", "broken"]
    ):
        """
        Change the status of the room.

        Parameters:
        status (Literal["cleaned", "used", "broken"]): The new status of the room.
            Must be one of the following values:
            - "cleaned": Indicates that the room has been cleaned.
            - "used": Indicates that the room is currently in use.
            - "broken": Indicates that the room is broken and needs maintenance.

        Returns:
        None
        """
        self.room_status = status

    def change_room_booking_status(self, status: Literal["booked", "empty"]):
        """
        Change the booking status of the room.

        Parameters:
        status (Literal['booked', 'empty']): The new booking status of the room.
            Must be one of the following values:
            - 'booked': Indicates that the room is currently booked.
            - 'empty': Indicates that the room is currently empty.

        Returns:
        None

        Example:
        change_room_booking_status('booked')
        Sets the room_booking_status to 'booked'.
        """
        self.room_booking_status = status

    class Meta(BaseModel.Meta):
        db_table = "room"

class RoomStatus(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "roomstatus"

class RoomKeepingAssign(BaseModel):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="maintenance_assignments",
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        related_name="room_keeping_assignments",
    )
    member_shift = models.ForeignKey(
        ProfileShiftAssign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="room_keeping_assignments",
    )
    assignment_date = models.DateField(default=timezone.now)
    assigned_to = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="room_keeping_duties",
    )
    priority = models.ForeignKey(
        "Priority",
        on_delete=models.SET_NULL,
        null=True,
        related_name="room_assignments",
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_roomkeeping_assignments",
    )
    last_modified_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_roomkeeping_assignments",
    )
    status = models.ManyToManyField(
        "HouseKeepingState",
        through="ProcessRoomKeeping",
        related_name="room_assignments",
    )
    current_status = models.CharField(max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    task_supported = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.assigned_to} - {self.shift} - [{self.room}]"

    @property
    def shift_period_ended(self):
        return self.member_shift.shift_end_time <= timezone.now()

    def change_status(self, new_status, created_by=None):
        with transaction.atomic():
            self.room_keeping_status_processes.create(
                room_number=self.room.room_number,
                status=HouseKeepingState.objects.get(name=new_status),
                created_by=created_by,
            )
            self.current_status = new_status

    # @property
    # def current_status(self):
    #     return self.room_keeping_status_processes.first().status.name

    @property
    def is_started(self):
        return self.room_keeping_status_processes.filter(
            status__name__iexact="ongoing"
        ).exists()

    class Meta(BaseModel.Meta):
        db_table = "roomkeepingassign"
        verbose_name = "Room Keeping Assignment"
        verbose_name_plural = "Room Keeping Assignments"
        ordering = ["-date_created"]

class HouseKeepingState(BaseModel):
    # options include: pending, ongoing, completed, faulty, request-for-help, confirm-completion
    name = models.CharField(max_length=255)
    allow_only_managers = models.BooleanField(default=False, null=True, blank=True)
    set_to_unfinished_after_task_expiry = models.BooleanField(
        default=False, null=True, blank=True
    )
    allow_after_task_is_ended = models.BooleanField(
        default=False, null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "housekeepingstate"
        verbose_name = "House-Keeping State"
        verbose_name_plural = "House-Keeping States"

class ProcessRoomKeeping(BaseModel):
    room_number = models.CharField(max_length=255)
    room_keeping_assign = models.ForeignKey(
        RoomKeepingAssign,
        on_delete=models.CASCADE,
        related_name="room_keeping_processes",
    )
    status = models.ForeignKey(HouseKeepingState, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room_number} - {self.status}"

    class Meta(BaseModel.Meta):
        db_table = "processroomkeeping"
        verbose_name = "Process Room Keeping"
        verbose_name_plural = "Process Room Keepings"

class ProcessRoomKeeping2(BaseModel):
    room_number = models.CharField(max_length=255)
    room_keeping_assign = models.ForeignKey(
        RoomKeepingAssign,
        on_delete=models.CASCADE,
        related_name="room_keeping_status_processes",
    )
    status = models.ForeignKey(HouseKeepingState, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room_number} - {self.status}"

    class Meta(BaseModel.Meta):
        db_table = "processroomkeeping2"
        verbose_name = "Process Room Keeping"
        verbose_name_plural = "Process Room Keepings"
        ordering = ["-date_created"]

class NameTitle(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    class Meta(BaseModel.Meta):
        db_table = "nametitle"
        verbose_name = "Title"
        verbose_name_plural = "Titles"

class IdentificationType(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "identificationtype"
        verbose_name = "Identification Type"
        verbose_name_plural = "Identification Types"

class Country(BaseModel):
    name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=255, blank=True, null=True)
    abbr = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)    

    def __str__(self):
        return f"{self.name} ({self.abbr})"

    class Meta(BaseModel.Meta):
        db_table = "country"
        verbose_name = "Country"
        verbose_name_plural = "Countries"

class Guest(BaseModel):
    guest_id = models.CharField(max_length=255, db_index=True, unique=True)
    title = models.ForeignKey(
        NameTitle, on_delete=models.SET_NULL, null=True, blank=True
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True, blank=True)
    # gender = models.CharField(max_length=255, choices=choices.GENDER_CHOICES)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    identification_type = models.ForeignKey(
        IdentificationType, on_delete=models.SET_NULL, null=True, blank=True
    )
    identification_number = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=255, blank=True, null=True)
    loyalty_programs = models.ManyToManyField(
        "LoyaltyProgram", through="GuestLoyaltyPrograms", related_name="guests"
    )

    def __str__(self):
        return (
            f"{self.title} {self.first_name} {self.last_name}"
            if self.title
            else f"{self.first_name} {self.last_name}"
        )
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta(BaseModel.Meta):
        db_table = "Guest"

class PaymentType(BaseModel):
    # eg. cash, credit
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "paymenttype"
        verbose_name = "Payment Type"
        verbose_name_plural = "Payment Types"

class SponsorType(BaseModel):
    # eg. self, corp, group
    name = models.CharField(max_length=255)
    allow_credit = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "sponsortype"
        verbose_name = "Sponsor Type"
        verbose_name_plural = "Sponsor Types"

class Sponsor(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    sponsor_type = models.ForeignKey(SponsorType, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "sponsor"

class PaymentMethod(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "paymentmethod"
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

class Receipt(BaseModel):
    issued_to = models.CharField(max_length=255)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=255, db_index=True)
    amount_paid = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    amount_available = models.DecimalField(
        max_digits=11, decimal_places=2, default=0.00
    )
    date_issued = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.SET_NULL, null=True
    )
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    receipt_status = models.CharField(
        max_length=255, choices=choices.RECEIPT_STATUS_CHOICES
    )

    def __str__(self):
        return self.receipt_number

    def can_pay(self, amount: float) -> bool:
        return self.amount_available >= amount

    def pay(self, amount: float):
        if not self.amount_available >= amount:
            raise serializers.ValidationError(
                {"error": "available balance on receipt is less than amount to be paid"}
            )
        self.amount_available -= amount

class Booking(BaseModel):
    # Guest-related fields
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
    guest_name = models.CharField(max_length=255, blank=True, null=True)
    # gender = models.CharField(max_length=255, choices=choices.GENDER_CHOICES)
    gender = models.CharField(max_length=12, null=True, blank=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # Room-related fields
    room_number = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, related_name="bookings"
    )
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True, related_name="bookings"
    )
    room_type = models.ForeignKey(
        RoomType, on_delete=models.SET_NULL, null=True, related_name="bookings"
    )

    # Booking-related fields
    booking_code = models.CharField(
        max_length=255, blank=True, null=True
    )  # this field is used in authenticating Guest complaints and requests
    vip_status = models.ForeignKey("VIPStatus", on_delete=models.SET_NULL, null=True)
    check_in_date = models.DateTimeField(default=timezone.now)
    check_out_date = models.DateTimeField(default=timezone.now)
    number_of_guests = models.PositiveIntegerField(default=1)
    number_of_older_guests = models.PositiveIntegerField(default=1)
    number_of_younger_guests = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    arrival_mode = models.ForeignKey(
        "ArrivalMode", on_delete=models.SET_NULL, null=True
    )
    rate = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    promo_code = models.CharField(max_length=255, blank=True, null=True)

    # payment information
    amount_paid = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    payment_status = models.ForeignKey(
        "PaymentStatus", on_delete=models.SET_NULL, null=True
    )
    receipt = models.ForeignKey(
        Receipt, on_delete=models.SET_NULL, null=True, blank=True
    )
    note = models.TextField(blank=True, null=True)

    date_created = models.DateTimeField(default=timezone.now, blank=True, null=True)
    date_modified = models.DateTimeField(default=timezone.now, blank=True, null=True)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_created",
    )
    modified_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_modified",
    )

    def __str__(self):
        return self.booking_code or f"Booking for {self.guest_name} in {self.room_number}"

    def extend_booking(self, num_days: int):
        """
        Extend the booking by num_days.
        Parameters:
        num_days (int): The number of days to extend the booking by.
        Returns:
        None
        """
        self.check_out = self.check_out + datetime.timedelta(days=num_days)

    def checkout(self):
        """
        Check out the Guest from the room.
        Parameters:
        None
        Returns:
        None
        """
        self.check_out = timezone.now()

    class Meta(BaseModel.Meta):
        db_table = "booking"

class ArrivalMode(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "arrivalmode"
        verbose_name = "Arrival Mode"
        verbose_name_plural = "Arrival Modes"

class VIPStatus(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "vipstatus"
        verbose_name = "VIP Status"
        verbose_name_plural = "VIP Statuses"

class LoyaltyProgram(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "loyaltyprogram"
        verbose_name = "Loyalty Program"
        verbose_name_plural = "Loyalty Programs"

class GuestLoyaltyPrograms(BaseModel):
    guest = models.ForeignKey(
        Guest, on_delete=models.CASCADE, related_name="my_loyalty_programs"
    )
    loyalty_program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.guest} - {self.loyalty_program}"

    class Meta(BaseModel.Meta):
        db_table = "Guestloyaltyprograms"
        verbose_name = "Guest Loyalty Program"
        verbose_name_plural = "Guest Loyalty Programs"

class Checkin(BaseModel):
    booking_code = models.CharField(max_length=255, db_index=True)
    guest = models.ForeignKey(
        Guest, on_delete=models.SET_NULL, null=True, blank=True, related_name="checkins"
    )
    guest_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=12, null=True, blank=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    room = models.ForeignKey(
        Room, on_delete=models.SET_NULL, null=True, related_name="checkins"
    )
    room_number = models.CharField(max_length=255, db_index=True)
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True
    )
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True)
    check_in_date = models.DateTimeField(default=timezone.now)
    number_of_older_guests = models.PositiveIntegerField(default=1)
    number_of_younger_guests = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    number_of_guests = models.PositiveIntegerField(default=1, blank=True, null=True)
    sponsor = models.ForeignKey(Sponsor, on_delete=models.SET_NULL, null=True)
    sponsor_name = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.ForeignKey(
        PaymentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    total_payment = models.DecimalField(
        max_digits=11, decimal_places=2, default=0.00, null=True
    )
    booking_payment_id = models.CharField(
        max_length=255, blank=True, null=True
    )  # field to store payment id for guests who have made payment for their booking
    check_out_date = models.DateTimeField(default=timezone.now)
    checked_out = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        db_table="checkin"
        verbose_name="Check-In"
        verbose_name_plural = "Check-Ins"

class CheckinPayment(BaseModel):
    check_in = models.ForeignKey(Checkin, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    receipt = models.ForeignKey(
        Receipt, on_delete=models.SET_NULL, null=True, blank=True
    )
    payment_timestamp = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "checkinpayment"
        verbose_name = "Check-In Payment"
        verbose_name_plural = "Check-In Payments"

class Checkout(BaseModel):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="checkout"
    )
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True)
    room_number = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True)
    date_checked_in = models.DateTimeField(default=timezone.now)
    date_checked_out = models.DateTimeField(default=timezone.now)
    checked_out_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name="checkouts"
    )
    checked_in_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name="checkins"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.booking} - {self.guest}"

    class Meta(BaseModel.Meta):
        db_table = "checkout"
        verbose_name = "Checkout"
        verbose_name_plural = "Checkouts"

class Priority(BaseModel):
    # eg. low, medium, high
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "priority"
        verbose_name = "Priority"
        verbose_name_plural = "Priorities"

class ComplaintStatus(BaseModel):
    # eg. pending, resolved, in-progress
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "complaintstatus"
        verbose_name = "Complaint Status"
        verbose_name_plural = "Complaint Statuses"

class Hashtag(BaseModel):
    # eg. #cleaning, #maintenance, #security
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(BaseModel.Meta):
        db_table = "hashtag"
        verbose_name = "Hashtag"
        verbose_name_plural = "Hashtags"

class Complaint(BaseModel):
    guest = models.CharField(max_length=255)
    room_number = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    # created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    complaint_items = models.ManyToManyField(Amenity)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True)
    status = models.ForeignKey(ComplaintStatus, on_delete=models.SET_NULL, null=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_complaints",
    )
    hashtags = models.ManyToManyField(Hashtag)

    def __str__(self):
        return f"{self.guest} - {self.room_number}"

    class Meta(BaseModel.Meta):
        db_table = "complaint"
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"

class AssignComplaint(BaseModel):
    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="assigned_complaints"
    )
    guest = models.CharField(max_length=255)
    room_number = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    assigned_to = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="complaints_assigned",
    )
    assigned_to_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True
    )
    date_assigned = models.DateTimeField(default=timezone.now)
    created_on = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_complaints",
    )
    complaint_status = models.ForeignKey(
        ComplaintStatus, on_delete=models.SET_NULL, null=True
    )
    updated_on = models.DateTimeField(null=True, blank=True)
    complaint_items = models.ManyToManyField(Amenity)
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True)
    hashtags = models.ManyToManyField(Hashtag)

    def __str__(self):
        return f"{self.complaint} - {self.assigned_to}"

    class Meta(BaseModel.Meta):
        db_table = "assigncomplaint"
        verbose_name = "Assign Complaint"
        verbose_name_plural = "Assign Complaints"
        ordering = ["-created_on"]

class ProcessComplaint(BaseModel):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_complaints",
    )
    assigned_complaint = models.ForeignKey(
        AssignComplaint, on_delete=models.SET_NULL, null=True
    )
    process_complaint_date = models.DateTimeField(default=timezone.now)
    processed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_complaints",
    )
    note = models.TextField()
    complaint_status = models.ForeignKey(
        ComplaintStatus,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_complaints",
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    # date_resolved = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.complaint} - {self.process_complaint_date}"

    class Meta(BaseModel.Meta):
        db_table = "processcomplaint"
        verbose_name = "Process Complaint"
        verbose_name_plural = "Process Complaints"

class SponsorClaims(BaseModel):
    sponsor = models.ForeignKey(Sponsor, on_delete=models.SET_NULL, null=True)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True)
    guest_name = models.CharField(max_length=255, blank=True, null=True)
    guest_department = models.CharField(max_length=255)
    guest_employment_id = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.sponsor} - {self.guest}"

    class Meta(BaseModel.Meta):
        db_table = "sponsorclaims"
        verbose_name = "Sponsor Claim"
        verbose_name_plural = "Sponsor Claims"

class PaymentStatus(BaseModel):
    # eg. pending, full-payment, part-payment
    name = models.CharField(max_length=255, db_index=True)

    class Meta(BaseModel.Meta):
        db_table = "paymentstatus"
        verbose_name = "Payment Status"
        verbose_name_plural = "Payment Statuses"
