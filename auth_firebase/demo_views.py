"""
Demo Mode Authentication Views

Provides session-based authentication bypass for demo mode deployment.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from workspaces.models import Workspace

logger = logging.getLogger(__name__)

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def demo_login(request):
    """
    Demo mode authentication endpoint.

    Creates a session for the demo user, bypassing Firebase authentication.
    Only works when DEMO_MODE environment variable is set to True.

    Returns:
        JSON response with demo user info and workspace:
        {
            "uid": "demo_user_uid",
            "is_authenticated": true,
            "auth_method": "demo_session",
            "workspace": {...}
        }
    """
    # Check if demo mode is enabled
    if not getattr(settings, "DEMO_MODE", False):
        return Response(
            {"error": "Demo mode is not enabled"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Get or create demo workspace
    demo_uid = "demo_user_deadline_2025"
    workspace, created = Workspace.objects.get_or_create(
        owner_uid=demo_uid,
        name="Demo Workspace",
        defaults={"description": "Demo workspace for exploring DEADLINE features"},
    )

    if created:
        logger.info("Created new demo workspace")

    # Set session data
    request.session["demo_mode"] = True
    request.session["demo_uid"] = demo_uid
    request.session["workspace_id"] = workspace.id

    response_data = {
        "uid": demo_uid,
        "is_authenticated": True,
        "auth_method": "demo_session",
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
        },
    }

    logger.info("Demo login successful for UID: %s", demo_uid)

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def demo_logout(request):
    """
    Demo mode logout endpoint.

    Clears the demo session data.

    Returns:
        JSON response confirming logout:
        {
            "message": "Logged out successfully"
        }
    """
    if request.session.get("demo_mode"):
        request.session.flush()
        logger.info("Demo logout successful")

    return Response(
        {"message": "Logged out successfully"},
        status=status.HTTP_200_OK,
    )
