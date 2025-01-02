import os
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
import uuid, datetime
from . import managers
from django.conf import settings
from utils.system_variables import PASSWORD_RESET
from utils import defaults, choices
from typing import Literal, Optional
from rest_framework import serializers

# Create your models here.


# Module defaults
# ROOM_STATUS_DEFAULT = defaults.get_table_default("roomstatus")


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    class Meta:
        abstract = True


class Department(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "department"


class Role(BaseModel):
    # headmaster, principal, teacher, cook, student, guardian
    name = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "role"


class CustomUser(AbstractBaseUser, BaseModel, PermissionsMixin):
    username = models.CharField(unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = managers.CustomUserManager()

    def has_perm(self, perm, obj=None):
        # Simplified permission check; customize as needed
        return True

    def has_module_perms(self, app_label):
        # Allow access to all app modules; customize as needed
        return True

    class Meta:
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

    class Meta:
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

    def __str__(self):
        return self.name

    class Meta:
        db_table = "gender"


class Profile(BaseModel):
    full_name = models.CharField(max_length=255)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name="profiles"
    )
    profile_roles = models.ManyToManyField(
        Role, through="ProfileRole", through_fields=("profile", "role")
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

    class Meta:
        db_table = "profile"


class ProfileRole(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="profiles")
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.profile.full_name} - [{self.role.name}]"

    class Meta:
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

    class Meta:
        db_table = "workshift"


class ProfileShiftAssign(BaseModel):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="shifts"
    )
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name="created_shifts"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name="modified_shifts"
    )
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{datetime.datetime.strftime(self.date, '%a %d %b %Y')} - {self.profile} - {self.shift}"

    class Meta:
        db_table = "profileshiftassign"
        verbose_name = "Shift Assignment"
        verbose_name_plural = "Shift Assignments"


class HotelFloor(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "hotelfloor"


class HotelView(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "hotelview"
        verbose_name = "Hotel View"
        verbose_name_plural = "Hotel Views"


class Amenity(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "amenities"
        verbose_name = "Amenity"
        verbose_name_plural = "Amenities"


class BedType(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
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

    class Meta:
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

    class Meta:
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
    amenities = models.ManyToManyField(Amenity)

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

    class Meta:
        db_table = "room"


class RoomStatus(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "roomstatus"


class RoomKeepingAssign(BaseModel):
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="maintenance_assignments"
    )
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True)
    assignment_date = models.DateField(default=timezone.now)
    assigned_to = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="room_keeping_duties",
    )
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
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.assigned_to} - {self.shift} - [{self.room}]"

    class Meta:
        db_table = "roomkeepingassign"
        verbose_name = "Room Keeping Assignment"
        verbose_name_plural = "Room Keeping Assignments"


class HouseKeepingState(BaseModel):
    # eg. waiting, used, assigned, cleaned, IP, faulty
    # when assignments are first created, the have the waiting-to-assigned state
    # when a user is checked in, the room state changes to ip-to-used
    # after checkout, the room state changes to used-to-waiting
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "housekeepingstate"
        verbose_name = "House-Keeping State"
        verbose_name_plural = "House-Keeping States"


class HouseKeepingStateTrans(BaseModel):
    # eg. waiting-to-assigned, used-to-waiting, assigned-to-cleaned, cleaned-to-IP, IP-to-used, assigned_to_faulty
    name = models.CharField(max_length=255, db_index=True)
    initial_trans_state = models.ForeignKey(
        HouseKeepingState, on_delete=models.CASCADE, related_name="initial_trans"
    )
    final_trans_state = models.ForeignKey(
        HouseKeepingState, on_delete=models.CASCADE, related_name="final_trans"
    )
    note = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.initial_trans_state} -> {self.final_trans_state}"

    class Meta:
        db_table = "housekeepingstatetrans"
        verbose_name = "House-Keeping State Transfer"
        verbose_name_plural = "House-Keeping State Transfers"


class ProcessRoomKeeping(BaseModel):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    room_keeping_assign = models.ForeignKey(RoomKeepingAssign, on_delete=models.CASCADE)
    room_state_trans = models.ForeignKey(
        HouseKeepingStateTrans, on_delete=models.SET_NULL, null=True
    )
    date_processed = models.DateTimeField(default=timezone.now)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        # returns the final trans state of the room
        return f"{self.room} - {self.room_state_trans.final_trans_state.name}"

    class Meta:
        db_table = "processroomkeeping"
        verbose_name = "Room Keeping"
        verbose_name_plural = "Room Keepings"


class NameTitle(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "nametitle"
        verbose_name = "Title"
        verbose_name_plural = "Titles"


class Client(BaseModel):
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
    national_id = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return (
            f"{self.title} {self.first_name} {self.last_name}"
            if self.title
            else f"{self.first_name} {self.last_name}"
        )

    class Meta:
        db_table = "client"


# DEFAULT_PAYMENT_TYPE = defaults.get_table_default('paymenttype')
class PaymentType(BaseModel):
    # eg. cash, credit
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "paymenttype"
        verbose_name = "Payment Type"
        verbose_name_plural = "Payment Types"


class SponsorType(BaseModel):
    # eg. self, corp, group
    name = models.CharField(max_length=255)
    allow_credit = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
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

    class Meta:
        db_table = "sponsor"


class PaymentMethod(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
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
    # Client-related fields
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.ForeignKey(
        NameTitle, on_delete=models.SET_NULL, null=True, blank=True
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    # gender = models.CharField(max_length=255, choices=choices.GENDER_CHOICES)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    employee_id = models.CharField(max_length=255, blank=True, null=True)
    group_id = models.CharField(max_length=255, blank=True, null=True)
    national_id = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=255, blank=True, null=True)

    # Room-related fields
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True
    )
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    room_number = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    # Booking-related fields
    booking_code = models.CharField(
        max_length=255, blank=True, null=True
    )  # this field is used in authenticating client complaints and requests
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(default=timezone.now)
    number_of_guests = models.PositiveIntegerField(default=1)
    number_of_older_guests = models.PositiveIntegerField(default=1)
    number_of_younger_guests = models.PositiveIntegerField(default=0)
    rate_type = models.CharField(
        max_length=255, choices=choices.RATE_TYPE_CHOICES, default="non-member"
    )
    rate = models.DecimalField(max_digits=11, decimal_places=2, default=0.00)
    promo_code = models.CharField(max_length=255, blank=True, null=True)

    # Sponsor and payment information
    sponsor_type = models.ForeignKey(
        SponsorType, on_delete=models.SET_NULL, null=True, blank=True
    )
    sponsor = models.ForeignKey(Sponsor, on_delete=models.SET_NULL, null=True)
    payment_type = models.ForeignKey(
        PaymentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    receipt = models.ForeignKey(
        Receipt, on_delete=models.SET_NULL, null=True, blank=True
    )

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
    checked_out = models.BooleanField(default=False)

    def __str__(self):
        return

    def extend_booking(self, num_days: datetime.datetime):
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
        Check out the client from the room.
        Parameters:
        None
        Returns:
        None
        """
        self.check_out = timezone.now()

    class Meta:
        db_table = "booking"


class Checkout(BaseModel):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="checkout"
    )
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
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
        return f"{self.booking} - {self.client}"

    class Meta:
        db_table = "checkout"
        verbose_name = "Checkout"
        verbose_name_plural = "Checkouts"


class Priority(BaseModel):
    # eg. low, medium, high
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "priority"
        verbose_name = "Priority"
        verbose_name_plural = "Priorities"


class ComplaintStatus(BaseModel):
    # eg. pending, resolved, in-progress
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "complaintstatus"
        verbose_name = "Complaint Status"
        verbose_name_plural = "Complaint Statuses"


class Hashtag(BaseModel):
    # eg. #cleaning, #maintenance, #security
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "hashtag"
        verbose_name = "Hashtag"
        verbose_name_plural = "Hashtags"


class Complaint(BaseModel):
    client = models.CharField(max_length=255)
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
        return f"{self.client} - {self.room_number}"

    class Meta:
        db_table = "complaint"
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"


class AssignComplaint(BaseModel):
    complaint = models.ForeignKey(
        Complaint, on_delete=models.CASCADE, related_name="assigned_complaints"
    )
    client = models.CharField(max_length=255)
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
    complaint_status = models.ForeignKey(ComplaintStatus, on_delete=models.SET_NULL, null=True)
    updated_on = models.DateTimeField(null=True, blank=True)
    complaint_items = models.ManyToManyField(Amenity)
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True)
    hashtags = models.ManyToManyField(Hashtag)

    def __str__(self):
        return f"{self.complaint} - {self.assigned_to}"

    class Meta:
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

    class Meta:
        db_table = "processcomplaint"
        verbose_name = "Process Complaint"
        verbose_name_plural = "Process Complaints"
