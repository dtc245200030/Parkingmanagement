"""API ViewSets cho quản lý Khu vực đỗ xe, Bảng giá và Vị trí đỗ xe trong bãi."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.parking.models import BangGia, KhuVuc, ParkingSpot
from apps.parking.serializers import BangGiaSerializer, KhuVucSerializer, ParkingSpotSerializer


class KhuVucViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý CRUD danh mục Khu vực đỗ xe và tính tổng quan tỷ lệ lấp đầy."""

    queryset = KhuVuc.objects.all().order_by("ma_khu_vuc")
    serializer_class = KhuVucSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """API lấy bức tranh tổng quan về tổng sức chứa, số chỗ đang đỗ, còn trống và tỷ lệ lấp đầy."""
        zones = self.get_queryset()
        serializer = self.get_serializer(zones, many=True)
        total_capacity = sum(z.suc_chua_toi_da for z in zones)
        total_occupied = sum(z["dang_gui"] for z in serializer.data)
        total_available = max(0, total_capacity - total_occupied)
        occupancy_rate = round((total_occupied / total_capacity * 100), 1) if total_capacity > 0 else 0.0

        return Response(
            {
                "total_capacity": total_capacity,
                "total_occupied": total_occupied,
                "total_available": total_available,
                "occupancy_rate": occupancy_rate,
                "zones": serializer.data,
            }
        )


class BangGiaViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý CRUD bảng giá dịch vụ cho từng loại xe."""

    queryset = BangGia.objects.all().select_related("loai_xe").order_by("ma_bang_gia")
    serializer_class = BangGiaSerializer
    permission_classes = [AllowAny]


class ParkingSpotViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý CRUD danh sách các vị trí đỗ xe cụ thể."""

    queryset = ParkingSpot.objects.all().select_related("khu_vuc").order_by("ma_vi_tri")
    serializer_class = ParkingSpotSerializer
    permission_classes = [AllowAny]

