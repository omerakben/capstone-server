"""
Demo Mode Authentication Middleware

Handles session-based authentication for demo mode, bypassing Firebase.
"""

import logging

from django.conf import settings

from .authentication import FirebaseUser

logger = logging.getLogger(__name__)


class DemoModeAuthenticationMiddleware:
    """
    Middleware to handle demo mode authentication.

    If DEMO_MODE is enabled and a demo session exists, authenticate the request
    with a FirebaseUser instance using the demo UID, bypassing Firebase token verification.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process if demo mode is enabled
        if getattr(settings, "DEMO_MODE", False):
            demo_mode = request.session.get("demo_mode", False)
            demo_uid = request.session.get("demo_uid")

            if demo_mode and demo_uid:
                # Create a FirebaseUser instance for the demo user
                request.user = FirebaseUser(uid=demo_uid)
                request.auth = {"demo": True}
                logger.debug("Demo mode authentication: UID=%s", demo_uid)

        response = self.get_response(request)
        return response
