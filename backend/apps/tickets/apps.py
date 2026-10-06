"""Cấu hình ứng dụng Django cho module quản lý vé xe và lượt gửi xe (tickets)."""

from django.apps import AppConfig


class TicketsConfig(AppConfig):
    """Cấu hình cho app tickets, quản lý thẻ vé, lượt xe vào/ra và vé tháng."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tickets"

