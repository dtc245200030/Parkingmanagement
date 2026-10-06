"""Cấu hình ứng dụng Django cho module lõi (core)."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Cấu hình cho app core, xử lý các tiện ích hệ thống dùng chung."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

