from api import models
from rest_framework import serializers


def check_profile_department(profile, department_name: str):
    try:
        deparment = models.Department.get(name=department_name)
        return profile.department == deparment
    except models.Department.DoesNotExist:
        raise serializers.ValidationError(
            {"error": f'Department with name "{department_name}" does not exist.'}
        )


def check_profile_role(profile, role_name: str):
    if not profile:
        return False
    return models.ProfileRole.objects.filter(
        profile=profile, role__name__in=[role_name], role__is_active=True
    ).exists()


def check_user_shift(date, profile, shift_name: str) -> bool:
    '''
    returns True if a user has a shift on a particular day
    for example check if user_A has a morning shift on '2025-01-01'.
    '''
    if not date:
        return False
    return models.ProfileShiftAssign.objects.filter(
        assignment_date=date, profile=profile, shift__name__iexact=shift_name
    ).exists()
