"""Cấu hình ứng dụng Django cho module quản lý loại xe và phương tiện (vehicles)."""

from django.apps import AppConfig


class VehiclesConfig(AppConfig):
    """Cấu hình cho app vehicles, quản lý danh mục loại xe và phương tiện."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.vehicles"

