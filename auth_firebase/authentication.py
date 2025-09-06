"""
Firebase Authentication for Django REST Framework

This module provides custom authentication classes for integrating Firebase Admin SDK
with Django REST Framework. It supports both real Firebase token verification and
mock authentication for local development.
"""

import logging
from typing import Optional, Tuple

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth

    FIREBASE_AVAILABLE = True
except ImportError:
    firebase_admin = None
    firebase_auth = None
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class FirebaseUser:
    """
    A user-like object that holds Firebase UID and authentication state.

    This mimics Django's User interface enough to work with DRF permissions
    while maintaining Firebase UID as the primary identifier.
    """

    def __init__(self, uid: str):
        self.uid = uid
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_active = True

    def __str__(self) -> str:
        return f"FirebaseUser(uid={self.uid})"

    def __repr__(self) -> str:
        return self.__str__()


class FirebaseAuthentication(BaseAuthentication):
    """
    Custom authentication class for Firebase JWT tokens.

    This class extends DRF's BaseAuthentication to verify Firebase ID tokens
    using the Firebase Admin SDK. It supports mock authentication for local
    development when Firebase is not available or configured.

    Expected header format:
        Authorization: Bearer <firebase_id_token>

    Returns:
        - (FirebaseUser, token) on successful authentication
        - None if no authentication is attempted

    Raises:
        - AuthenticationFailed for invalid tokens or authentication errors
    """

    keyword = "Bearer"
    model = None

    def authenticate(self, request) -> Optional[Tuple[FirebaseUser, str]]:
        """
        Authenticate the request and return a two-tuple of (user, token).

        Args:
            request: The HTTP request object

        Returns:
            Tuple of (FirebaseUser, token) if authentication succeeds,
            None if no authentication is attempted

        Raises:
            AuthenticationFailed: If authentication fails
        """
        auth_header = self.get_authorization_header(request)
        if not auth_header:
            return None

        auth_token = self.get_raw_token(auth_header)
        if auth_token is None:
            return None

        return self.get_validated_user(auth_token)

    def get_authorization_header(self, request) -> Optional[str]:
        """Extract the Authorization header from the request."""
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return None
        return auth_header

    def get_raw_token(self, auth_header: str) -> Optional[str]:
        """
        Extract the token from the Authorization header.

        Args:
            auth_header: The full Authorization header value

        Returns:
            The raw token string or None if invalid format
        """
        parts = auth_header.split()

        if len(parts) != 2:
            return None

        if parts[0] != self.keyword:
            return None

        return parts[1]

    def get_validated_user(self, raw_token: str) -> Tuple[FirebaseUser, str]:
        """
        Validate the token and return user and token.

        Args:
            raw_token: The Firebase ID token to validate

        Returns:
            Tuple of (FirebaseUser, token)

        Raises:
            AuthenticationFailed: If token validation fails
        """
        # Enforce real Firebase authentication only
        return self.get_firebase_user(raw_token)

    # Removed mock authentication helpers (should_use_mock_auth, get_mock_user)
    # to prevent accidental usage. Any attempt to run without Firebase Admin
    # now raises an authentication failure.

    def get_firebase_user(self, raw_token: str) -> Tuple[FirebaseUser, str]:
        """
        Validate token with Firebase Admin SDK and create user.

        Args:
            raw_token: The Firebase ID token to validate

        Returns:
            Tuple of (FirebaseUser, token)

        Raises:
            AuthenticationFailed: If token validation fails
        """
        if not FIREBASE_AVAILABLE or firebase_auth is None:
            raise AuthenticationFailed(
                "Firebase Admin SDK is not available. "
                "Install firebase-admin or enable mock authentication."
            )

        try:
            # Verify the ID token with Firebase Admin SDK
            decoded_token = firebase_auth.verify_id_token(raw_token)
            uid = decoded_token["uid"]

            logger.info("✅ Firebase token verified for UID: %s", uid)

            user = FirebaseUser(uid=uid)
            return (user, raw_token)

        except Exception as e:
            # Handle all Firebase exceptions generically
            logger.warning("❌ Firebase authentication error: %s", str(e))
            raise AuthenticationFailed(
                f"Firebase authentication failed: {str(e)}"
            ) from e

    def authenticate_header(self, _request):
        """
        Return the WWW-Authenticate header for unauthenticated responses.

        This is used by DRF to set the appropriate authentication challenge
        in 401 responses. Returns None to maintain compatibility with BaseAuthentication.
        """
        # DRF BaseAuthentication returns None by default
        # Custom authentication schemes that want WWW-Authenticate headers
        # typically handle this through middleware or view-level logic
        return None
