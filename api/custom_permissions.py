from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Profile
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
