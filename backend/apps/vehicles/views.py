"""ViewSets quản lý các thao tác CRUD danh mục Loại xe và Phương tiện."""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.vehicles.models import LoaiXe, PhuongTien
from apps.vehicles.serializers import LoaiXeSerializer, PhuongTienSerializer


class LoaiXeViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý danh mục các Loại xe được hỗ trợ trong bãi đỗ."""

    queryset = LoaiXe.objects.all().order_by("ma_loai_xe")
    serializer_class = LoaiXeSerializer
    permission_classes = [AllowAny]


class PhuongTienViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý danh sách các Phương tiện từng gửi trong bãi."""

    queryset = PhuongTien.objects.all().select_related("loai_xe").order_by("-ma_phuong_tien")
    serializer_class = PhuongTienSerializer
    permission_classes = [AllowAny]

