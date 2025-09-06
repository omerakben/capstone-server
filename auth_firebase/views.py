"""
Authentication Views for Firebase Integration

This module provides API views for Firebase authentication, including user information
endpoints and token verification.
"""

import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .authentication import FirebaseUser
from .permissions import IsAuthenticated

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    """
    Get current authenticated user information.

    Returns Firebase UID and authentication status for the current user.
    This endpoint is useful for frontend applications to verify authentication
    and get user identity information.

    Returns:
        JSON response with user information:
        {
            "uid": "firebase_user_uid",
            "is_authenticated": true,
            "auth_method": "firebase"
        }
    """
    user = request.user

    if not isinstance(user, FirebaseUser):
        logger.error("User info requested but user is not FirebaseUser instance")
        return Response(
            {"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST
        )

    user_data = {
        "uid": user.uid,
        "is_authenticated": user.is_authenticated,
        "auth_method": "firebase",
    }

    logger.info("User info requested for UID: %s", user.uid)

    return Response(user_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Verify the current Firebase token.

    This endpoint can be used to check if the current token is still valid.
    Since the request reaches this view, the token has already been verified
    by the FirebaseAuthentication class.

    Returns:
        JSON response confirming token validity:
        {
            "valid": true,
            "uid": "firebase_user_uid",
            "token_type": "firebase_id_token"
        }
    """
    user = request.user
    # Token is available in request.auth but not needed for this endpoint

    if not isinstance(user, FirebaseUser):
        logger.error(
            "Token verification requested but user is not FirebaseUser instance"
        )
        return Response(
            {"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST
        )

    verification_data = {
        "valid": True,
        "uid": user.uid,
        "token_type": "firebase_id_token",
        "verified_at": "server_side",
    }

    logger.info("Token verification successful for UID: %s", user.uid)

    return Response(verification_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):  # pylint: disable=unused-argument
    """
    Health check endpoint for authentication system.

    This endpoint doesn't require authentication and can be used to verify
    that the authentication system is properly configured.

    Returns:
        JSON response with authentication system status:
        {
            "status": "healthy",
            "firebase_available": true/false,
            "mock_auth_enabled": true/false
        }
    """
    from django.conf import settings

    from .authentication import FIREBASE_AVAILABLE

    health_data = {
        "status": "healthy",
        "firebase_available": FIREBASE_AVAILABLE,
        "debug_mode": settings.DEBUG,
    }

    return Response(health_data, status=status.HTTP_200_OK)
