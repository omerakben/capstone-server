"""
URL configuration for Firebase authentication app.

This module defines the URL patterns for authentication-related endpoints.
"""

from django.urls import path

from . import views

app_name = "auth_firebase"

urlpatterns = [
    # User information endpoint
    path("user/", views.user_info, name="user_info"),
    # Token verification endpoint
    path("verify/", views.verify_token, name="verify_token"),
    # Health check endpoint
    path("health/", views.health_check, name="health_check"),
]
