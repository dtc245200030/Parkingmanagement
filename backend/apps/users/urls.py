"""Định tuyến các đường dẫn API quản lý người dùng và vai trò (/api/users/)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import NguoiDungViewSet, VaiTroViewSet

router = DefaultRouter()
router.register(r"roles", VaiTroViewSet, basename="vaitro")
router.register(r"", NguoiDungViewSet, basename="nguoidung")

urlpatterns = [
    path("", include(router.urls)),
]

