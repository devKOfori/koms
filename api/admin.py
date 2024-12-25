from django.contrib import admin
from . import models

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = ('username', 'first_name', 'last_name', 'password', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = ('username', 'first_name', 'last_name', 'password', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        user = super().save(commit=False)
        # Check if the password is being updated
        if self.cleaned_data["password"] and not user.password.startswith("pbkdf2_"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = models.CustomUser

    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'password', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(models.CustomUser, CustomUserAdmin)
admin.site.register(models.Department)
admin.site.register(models.Gender)
admin.site.register(models.ProfileRole)
admin.site.register(models.Profile)
admin.site.register(models.Role)
admin.site.register(models.HotelFloor)
admin.site.register(models.HotelView)
admin.site.register(models.RoomCategory)
admin.site.register(models.RoomType)
admin.site.register(models.Room)
admin.site.register(models.Amenity)
admin.site.register(models.Shift)
admin.site.register(models.ProfileShiftAssign)