"""
Custom Permissions for Firebase Authentication

This module provides permission classes for row-level security based on Firebase UID.
It ensures that users can only access resources they own.
"""

import logging

from rest_framework.permissions import BasePermission

from .authentication import FirebaseUser

logger = logging.getLogger(__name__)


class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to access it.

    This permission checks if the requesting user owns the object by comparing
    Firebase UIDs. It handles both direct ownership (objects with owner_uid field)
    and indirect ownership (objects related to workspaces with owner_uid).

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwner]
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the specific object.

        This method checks ownership by comparing Firebase UIDs. It handles:
        1. Direct ownership: obj.owner_uid == request.user.uid
        2. Workspace ownership: obj.workspace.owner_uid == request.user.uid
        3. Other relationship patterns as needed

        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            True if user owns the object, False otherwise
        """
        # Authentication is handled by IsAuthenticated permission class
        user_uid = request.user.uid

        # Case 1: Direct ownership (e.g., Workspace model)
        if hasattr(obj, "owner_uid"):
            is_owner = obj.owner_uid == user_uid
            if not is_owner:
                logger.warning(
                    "IsOwner permission denied: Direct ownership check failed. "
                    "Object owner_uid: %s, User UID: %s",
                    obj.owner_uid,
                    user_uid,
                )
            return is_owner

        # Case 2: Workspace relationship (e.g., Artifact model)
        if hasattr(obj, "workspace") and hasattr(obj.workspace, "owner_uid"):
            is_owner = obj.workspace.owner_uid == user_uid
            if not is_owner:
                logger.warning(
                    "IsOwner permission denied: Workspace ownership check failed. "
                    "Workspace owner_uid: %s, User UID: %s",
                    obj.workspace.owner_uid,
                    user_uid,
                )
            return is_owner

        # Case 3: Other relationship patterns can be added here
        # For example, if there are nested relationships like:
        # if hasattr(obj, 'parent') and hasattr(obj.parent, 'workspace'):
        #     return obj.parent.workspace.owner_uid == user_uid

        # If no ownership pattern is found, deny access for security
        logger.warning(
            "IsOwner permission denied: No ownership pattern found for object type %s",
            type(obj).__name__,
        )
        return False


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission that allows read access to any user but write access only to owners.

    This extends IsOwner to provide more granular control, allowing GET/HEAD/OPTIONS
    for any authenticated user while restricting POST/PUT/PATCH/DELETE to owners.

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    """

    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.

        Args:
            request: The HTTP request object
            view: The view being accessed

        Returns:
            True if user is authenticated with Firebase, False otherwise
        """
        # Must be authenticated with Firebase for any access
        return (
            request.user
            and hasattr(request.user, "uid")
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the specific object.

        Read permissions (GET, HEAD, OPTIONS) are allowed for any authenticated user.
        Write permissions (POST, PUT, PATCH, DELETE) require ownership.

        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            True if user has appropriate access, False otherwise
        """
        # Must be authenticated with Firebase
        if not self.has_permission(request, view):
            return False

        # Read permissions for any authenticated user
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Write permissions require ownership (delegate to IsOwner)
        is_owner_permission = IsOwner()
        return is_owner_permission.has_object_permission(request, view, obj)


class IsAuthenticated(BasePermission):
    """
    Simple authentication check for Firebase users.

    This is similar to DRF's IsAuthenticated but specifically checks for Firebase
    authentication attributes.

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated]
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated with Firebase.

        Args:
            request: The HTTP request object
            view: The view being accessed

        Returns:
            True if user is authenticated with Firebase, False otherwise
        """
        return (
            request.user
            and isinstance(request.user, FirebaseUser)
            and request.user.is_authenticated
        )
