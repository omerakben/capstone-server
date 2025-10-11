"""
URL configuration for Firebase authentication app.

This module defines the URL patterns for authentication-related endpoints.
"""

from django.urls import path

from . import demo_views, views

app_name = "auth_firebase"

urlpatterns = [
    # User information endpoint
    path("user/", views.user_info, name="user_info"),
    # Token verification endpoint
    path("verify/", views.verify_token, name="verify_token"),
    # Health check endpoint
    path("health/", views.health_check, name="health_check"),
    # Demo mode endpoints
    path("demo/login/", demo_views.demo_login, name="demo_login"),
    path("demo/logout/", demo_views.demo_logout, name="demo_logout"),
]
