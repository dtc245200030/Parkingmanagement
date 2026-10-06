"""Định tuyến các đường dẫn API cho module xác thực tài khoản (login, logout, register, me)."""

from django.urls import path
from apps.authentication.views import login_view, logout_view, me_view, register_view

urlpatterns = [
    path("login/", login_view, name="auth-login"),
    path("register/", register_view, name="auth-register"),
    path("logout/", logout_view, name="auth-logout"),
    path("me/", me_view, name="auth-me"),
]

