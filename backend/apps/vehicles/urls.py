"""Định tuyến các đường dẫn API quản lý loại xe và phương tiện (/api/vehicle-types/, /api/vehicles/)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.vehicles.views import LoaiXeViewSet, PhuongTienViewSet

router = DefaultRouter()
router.register(r"types", LoaiXeViewSet, basename="loaixe")
router.register(r"vehicles", PhuongTienViewSet, basename="phuongtien")
router.register(r"", LoaiXeViewSet, basename="loaixe-default")

urlpatterns = [
    path("", include(router.urls)),
]

