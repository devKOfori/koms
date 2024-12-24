import os
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
import uuid
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
    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "role"


class CustomUser(AbstractBaseUser):
    username = models.CharField(unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = managers.CustomUserManager()

    def has_perm(self, perm, obj=None):
        # Simplified permission check; customize as needed
        return True

    def has_module_perms(self, app_label):
        # Allow access to all app modules; customize as needed
        return True


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
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    role = models.ManyToManyField(
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
