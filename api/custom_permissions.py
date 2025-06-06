from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Profile, Department, CustomUser
class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Custom permission to only allow authenticated users to edit objects.
    Unauthenticated users can only read objects.
    """

    def has_permission(self, request, view) -> bool:
        # Allow read-only access for unauthenticated users
        if request.method in SAFE_METHODS:
            return True
        # Allow write access for authenticated users
        return request.user and request.user.is_authenticated   

class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        """
        Custom permission to only allow admin users to access the view.
        This permission is used to restrict access to views that require admin privileges.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return False
        return profile.has_role("Admin")

class IsDepartmentExec(BasePermission):
    def has_permission(self, request, view):
        """
        Custom permission to allow access only to users with the 'Department Exec' role.
        This permission is used to restrict access to views that require department executive privileges.
        """
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return False
        
        return profile.roles.exists() and not profile.has_role("Staff")

class IsAddingProfileToOwnDepartment(BasePermission):
    def has_permission(self, request, view):
        assigned_department = request.data.get("department")
        try:
            profile = request.user.profile
            if not profile.department:
                return False
        except Profile.DoesNotExist:
            return False
        
        return profile.department.name == assigned_department or profile.has_role("Admin")

class IsAdminProfileOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """

    def has_permission(self, request, view) -> bool:
        '''
        Check if the user is authenticated and has the 'admin' role.
        This permission is used to restrict access to views that require admin privileges.
        '''
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in SAFE_METHODS:
            return True
        
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return False
        # Check if the user has the 'admin' role or is a superuser
        return profile.has_role("admin") or request.user.is_superuser

class CanAddNewUserToDepartment(BasePermission):
    def has_permission(self, request, view) -> bool:
        """
        Allows access if the user is authenticated and either:
        - Belongs to the department they're trying to assign
        - Or has the 'Admin' role
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            profile = Profile.objects.select_related("department").prefetch_related("profile_roles").get(user=request.user)
            # Ensure the user has roles assigned
            # If the user has no roles or is a staff member, deny access
            if not profile.roles.exists() or profile.has_role("Staff"):
                return False
        except Profile.DoesNotExist:
            return False
        
        department_name = request.data.get("department")
        if not department_name:
            return False
        
        try:
            department = Department.objects.get(name=department_name)
        except Department.DoesNotExist:
            return False
        
        # Check if the user has the 'manage_department_profiles' role
        return profile.department == department or profile.has_role("Admin")
    

class CanViewUserProfileRoles(BasePermission):
    def has_permission(self, request, view) -> bool:
        user: CustomUser = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            profile = user.profile
            if not profile.roles.exists() or profile.has_role("Staff"):
                return False
        except Profile.DoesNotExist:
            return False
        return (
            str(profile.id) == str(view.kwargs.get("pk")) or 
            profile.has_role("Admin") or
            profile.has_role("Supervisor") or
            profile.has_
        )
    
class IsHouseKeepingStaff(BasePermission):
    def has_permission(self, request, view):
        """
        Custom permission to allow access only to users with the 'House Keeping' role.
        This permission is used to restrict access to views that require house keeping privileges.
        """
        try:
            profile: Profile = request.user.profile
        except Profile.DoesNotExist:
            return False
        
        return profile.is_member_of("Housekeeping")
    
class IsFrontDeskStaff(BasePermission):
    def has_permission(self, request, view):
        """
        Custom permission to allow access only to users with the 'Front Desk' role.
        This permission is used to restrict access to views that require front desk privileges.
        """
        try:
            profile: Profile = request.user.profile
        except Profile.DoesNotExist:
            return False
        
        return profile.is_member_of("Frontdesk")
    
class IsHouseKeepingStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        """
        Custom permission to allow read-only access for all users,
        but restrict write access to house keeping staff or admin users.
        """
        if request.method in SAFE_METHODS:
            return True
        
        try:
            profile: Profile = request.user.profile
        except Profile.DoesNotExist:
            return False
        
        return profile.is_member_of("Housekeeping") or profile.has_role("Admin")