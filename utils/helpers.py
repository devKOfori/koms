from api import models
from rest_framework import serializers
from django.contrib.auth.models import Group
from django.apps import apps
from django.db import transaction

def is_valid_password(password: str) -> bool:
    """
    Validates the password to ensure it meets the required criteria.
    Args:
        password (str): The password to validate.
    Returns:
        bool: True if the password meets the specified criteria, False otherwise.
    """
    return True

def check_profile_department(profile, department_name: str):
    try:
        deparment = models.Department.objects.get(name__iexact=department_name)
        return profile.department == deparment
    except models.Department.DoesNotExist:
        raise serializers.ValidationError(
            {"error": f'Department with name "{department_name}" does not exist.'}
        )


def check_profile_role(profile, role_name: str) -> bool:
    if not profile:
        return False
    return models.ProfileRole.objects.filter(
        profile=profile, role__name__in=[role_name], is_active=True
    ).exists()


def check_user_shift(date, profile, shift_name: str) -> bool:
    '''
    returns True if a user has a shift on a particular day
    for example check if user_A has a morning shift on '2025-01-01'.
    '''
    print(f'date: {date}, profile: {profile}, shift_name: {shift_name}')
    if not date:
        return False
    return models.ProfileShiftAssign.objects.filter(
        date=date, profile=profile, shift__name__iexact=shift_name
    ).exists()


def set_profile_groups(profile, group_names_list:list) -> str:
    print('in set profile groups')
    '''
    Sets the given profile groups to the groups specified.
    Args:
        profile: A user profile instance.
        group_names_list (list): List of group names to assign to the profile.
    Returns:
        dict: A success message if the operation succeeds.

    Raises:
        ValidationError: If any error occurs during the operation.
    '''
    try:
        groups_list = Group.objects.filter(name__in=group_names_list)
        if not groups_list.exists():
            raise serializers.ValidationError({'error': 'No matching groups found for the provided names.'})
        user = profile.user
        # print(f'user groups: {user.groups.all()}')
        user.groups.set(groups_list)
        return "success"
    except Group.DoesNotExist:
        raise serializers.ValidationError({'error': 'One or more groups do not exist.'})
    except Exception as e:
        raise serializers.ValidationError({'error': f'an unexpected error occured: {str(e)}'})

def set_profile_roles(profile, roles_data:list) -> str:
    
    '''
    Sets the given profile roles to the roles specified.
    Args:
        profile: A user profile instance.
        role_names_list (list): List of role names to assign to the profile.
    Returns:
        dict: A success message if the operation succeeds.

    Raises:
        ValidationError: If any error occurs during the operation.
    '''
    try:
        roles_list = [role_data['role'] for role_data in roles_data]
        if not roles_list:
            raise serializers.ValidationError({'error': 'No matching roles found for the provided names.'})
        
        models.ProfileRole.objects.bulk_create(
            [
                models.ProfileRole(
                    profile=profile,
                    role=role,
                    is_active=role_data.get("is_active", True),
                )
                for role, role_data in zip(roles_list, roles_data)
            ]
        )
        return "success"
    except models.Role.DoesNotExist:
        raise serializers.ValidationError({'error': 'One or more roles do not exist.'})
    except Exception as e:
        raise serializers.ValidationError({'error': f'an unexpected error occured: {str(e)}'})
    
def checkout_booking(booking, checked_out_by):
    '''
    Checks out a booking and updates the room status.
    Args:
        booking: A booking instance.
        checked_out_by: A user profile instance.
    Returns:
        str: A success message if the operation succeeds.
    Raises:
        ValidationError: If any error occurs during the operation.
    '''
    try:
        with transaction.atomic():
            booking.checked_out = True
            room = booking.room
            room.room_booking_status = "empty"
            room.room_maintenance_status = "used"
            room.save()
            booking.checked_out = True
            booking.save()
            Checkout = apps.get_model('api', 'Checkout')
            Checkout.objects.create(
                booking=booking,
                room_number=room.room_number,
                client=booking.client,
                first_name=booking.first_name,
                last_name=booking.last_name,
                gender=booking.gender,
                date_checked_in=booking.check_in,
                date_checked_out=booking.check_out,
                checked_out_by=checked_out_by,
                checked_in_by=booking.created_by,
            )
        return "success"
    except Exception as e:
        raise serializers.ValidationError({'error': f'an unexpected error occured: {str(e)}'})
    
def get_room_type_current_price(room_type: models.RoomType) -> float:
    """
    Retrieves the current price of a room type.
    
    Args:
        room_type (models.RoomType): The room type instance.
        
    Returns:
        float: The current price of the room type.
    """
    return room_type.base_price

def calculate_booking_cost(booking: models.Booking) -> float:
    booking_duration = (booking.check_out_date - booking.check_in_date).days
    cost_per_day = get_room_type_current_price(booking.room_type)
    total_cost = booking_duration * cost_per_day
    return total_cost