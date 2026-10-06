"""Cấu hình ứng dụng Django cho module báo cáo và thống kê (reports)."""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Cấu hình cho app reports, tổng hợp dữ liệu báo cáo và xuất file Excel."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"

