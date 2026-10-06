"""Cấu hình định tuyến alias đường dẫn API dành riêng cho vị trí đỗ xe (/api/parking-spots/)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.parking.views import ParkingSpotViewSet

router = DefaultRouter()
router.register(r"", ParkingSpotViewSet, basename="parkingspot-spot")

urlpatterns = [
    path("", include(router.urls)),
]

