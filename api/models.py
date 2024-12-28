import os
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
import uuid, datetime
from . import managers
from django.conf import settings
from utils.system_variables import PASSWORD_RESET

# Create your models here.


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


PASSWORD_RESET_CHANNEL_CHOICES = [("email", "Email"), ("sms", "SMS")]


class PasswordReset(BaseModel):
    username = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    reset_channel = models.CharField(
        max_length=30, choices=PASSWORD_RESET_CHANNEL_CHOICES
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


class RoomCategory(BaseModel):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "roomcategory"
        verbose_name = "Room Category"
        verbose_name_plural = "Room Categories"


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
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "amenities"
        verbose_name = "Amenity"
        verbose_name_plural = "Amenities"


class RoomType(BaseModel):
    name = models.CharField(max_length=255)
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True, related_name='room_types'
    )
    area_in_meters = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    area_in_feet = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    max_guests = models.IntegerField(default=1)
    bed = models.CharField(max_length=255)
    view = models.ForeignKey(HotelView, on_delete=models.SET_NULL, null=True)
    amenities = models.ManyToManyField(Amenity)
    price_per_night = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
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
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, related_name='rooms')
    price_per_night = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    is_occupied = models.BooleanField(default=False)
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.room_number

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
    # eg. used, assigned, cleaned, IP, faulty
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "housekeepingstate"
        verbose_name = "House-Keeping State"
        verbose_name_plural = "House-Keeping States"


class HouseKeepingStateTrans(BaseModel):
    # eg. used-to-assigned, assigned-to-cleaned, cleaned-to-IP, IP-to-used, assigned_to_faulty
    name=models.CharField(max_length=255)
    initial_trans_state = models.ForeignKey(
        HouseKeepingState, on_delete=models.CASCADE, related_name="initial_trans"
    )
    final_trans_state = models.ForeignKey(
        HouseKeepingState, on_delete=models.CASCADE, related_name="final_trans"
    )
    note=models.CharField(max_length=255, blank=True, null=True)
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

    def __str__(self):
        # returns the final trans state of the room
        return f"{self.room} - {self.room_state_trans.to_state.name}"

    class Meta:
        db_table = "processroomkeeping"
        verbose_name = "Room Keeping"
        verbose_name_plural = "Room Keepings"


class Booking(BaseModel):
    check_in = models.DateField(default=timezone.now)
    check_out = models.DateField(default=timezone.now)
    room_category = models.ForeignKey(
        RoomCategory, on_delete=models.SET_NULL, null=True
    )
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "booking"
