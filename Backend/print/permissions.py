# permissions.py
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow users to edit their own profile or admins to edit any profile.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner or staff
        return obj == request.user or request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Only admin users can modify data. Others can only read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        return request.user.is_staff
