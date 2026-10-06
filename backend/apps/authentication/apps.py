"""Cấu hình ứng dụng Django cho module xác thực tài khoản (authentication)."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Cấu hình cho app authentication, khởi tạo các thông số tự động của ứng dụng."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"

