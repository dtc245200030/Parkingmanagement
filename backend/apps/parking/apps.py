"""Cấu hình ứng dụng Django cho module quản lý khu vực đỗ xe và bảng giá (parking)."""

from django.apps import AppConfig


class ParkingConfig(AppConfig):
    """Cấu hình cho app parking, quản lý khu vực, vị trí và bảng tính phí."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.parking"

