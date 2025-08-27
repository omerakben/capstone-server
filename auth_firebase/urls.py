"""
URLs for auth_firebase app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("verify/", views.VerifyTokenView.as_view(), name="verify-token"),
    path("user/", views.UserInfoView.as_view(), name="user-info"),
]
