"""Cấu hình định tuyến alias đường dẫn API dành riêng cho bảng giá gửi xe (/api/pricing-rules/)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.parking.views import BangGiaViewSet

router = DefaultRouter()
router.register(r"", BangGiaViewSet, basename="banggia-pricing")

urlpatterns = [
    path("", include(router.urls)),
]

