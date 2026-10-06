"""Định tuyến đường dẫn kiểm tra sức khỏe hệ thống (health check)."""

from django.urls import path
from apps.core.views import health_check

urlpatterns = [
    path("", health_check, name="health-check"),
]

