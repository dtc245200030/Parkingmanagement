"""Cấu hình định tuyến API cho khu vực đỗ xe, vị trí đỗ và bảng giá trong app parking."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.parking.views import BangGiaViewSet, KhuVucViewSet, ParkingSpotViewSet

router = DefaultRouter()
router.register(r"zones", KhuVucViewSet, basename="khuvuc")
router.register(r"spots", ParkingSpotViewSet, basename="parkingspot")
router.register(r"pricing", BangGiaViewSet, basename="banggia")
router.register(r"", KhuVucViewSet, basename="khuvuc-default")

urlpatterns = [
    path("", include(router.urls)),
]

