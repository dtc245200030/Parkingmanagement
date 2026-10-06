"""Serializers cho các mô hình Khu vực đỗ xe, Bảng giá và Vị trí đỗ xe."""

from rest_framework import serializers
from apps.parking.models import BangGia, KhuVuc, ParkingSpot
from apps.vehicles.serializers import LoaiXeSerializer


class KhuVucSerializer(serializers.ModelSerializer):
    """Serializer dữ liệu cho khu vực đỗ xe kèm thông tin số lượng xe đang gửi, còn trống và công suất."""

    tong_so_cho = serializers.IntegerField(source="suc_chua_toi_da", read_only=True)
    dang_gui = serializers.SerializerMethodField()
    con_trong = serializers.SerializerMethodField()
    cong_suat = serializers.SerializerMethodField()

    class Meta:
        model = KhuVuc
        fields = [
            "ma_khu_vuc",
            "ten_khu_vuc",
            "suc_chua_toi_da",
            "tong_so_cho",
            "mo_ta",
            "dang_gui",
            "con_trong",
            "cong_suat",
        ]

    def get_dang_gui(self, obj):
        """Tính tổng số lượt gửi xe đang active trong khu vực."""
        from apps.tickets.models import LuotGuiXe
        count = LuotGuiXe.objects.filter(
            trang_thai_luot="Đang gửi",
            khu_vuc=obj
        ).count()
        return count

    def get_con_trong(self, obj):
        """Tính số chỗ còn trống trong khu vực."""
        dang_gui = self.get_dang_gui(obj)
        return max(0, obj.suc_chua_toi_da - dang_gui)

    def get_cong_suat(self, obj):
        """Tính phần trăm công suất sử dụng của khu vực đỗ xe."""
        dang_gui = self.get_dang_gui(obj)
        if obj.suc_chua_toi_da > 0:
            return round((dang_gui / obj.suc_chua_toi_da) * 100, 1)
        return 0.0


class BangGiaSerializer(serializers.ModelSerializer):
    """Serializer quản lý thông tin cấu hình bảng giá gửi xe."""

    ten_loai_xe = serializers.CharField(source="loai_xe.ten_loai_xe", read_only=True)
    loai_xe_detail = LoaiXeSerializer(source="loai_xe", read_only=True)

    class Meta:
        model = BangGia
        fields = [
            "ma_bang_gia",
            "loai_xe",
            "ten_loai_xe",
            "loai_xe_detail",
            "loai_ap_dung",
            "gia_co_ban",
            "don_vi_thoi_gian_phut",
            "gia_tang_them",
            "gia_ban_dem",
            "ngay_ap_dung",
        ]


class ParkingSpotSerializer(serializers.ModelSerializer):
    """Serializer quản lý thông tin chi tiết từng vị trí đỗ xe."""

    khu_vuc_name = serializers.CharField(source="khu_vuc.ten_khu_vuc", read_only=True)

    class Meta:
        model = ParkingSpot
        fields = ["ma_vi_tri", "code", "khu_vuc", "khu_vuc_name", "area", "status"]

