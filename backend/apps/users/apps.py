"""Cấu hình ứng dụng Django cho module quản lý người dùng và phân quyền (users)."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Cấu hình cho app users, quản lý người dùng, nhân viên và vai trò."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "Quản lý Người dùng & Nhân viên"

