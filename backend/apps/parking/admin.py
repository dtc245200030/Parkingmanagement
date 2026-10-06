"""Cấu hình giao diện Admin cho các mô hình Khu vực đỗ xe, Bảng giá và Vị trí đỗ xe."""

from django.contrib import admin
from apps.parking.models import BangGia, KhuVuc, ParkingSpot


@admin.register(KhuVuc)
class KhuVucAdmin(admin.ModelAdmin):
    """Cấu hình trang quản trị Admin cho danh mục Khu vực đỗ xe."""

    list_display = ("ma_khu_vuc", "ten_khu_vuc", "suc_chua_toi_da", "mo_ta")
    search_fields = ("ten_khu_vuc",)


@admin.register(BangGia)
class BangGiaAdmin(admin.ModelAdmin):
    """Cấu hình trang quản trị Admin cho Bảng giá dịch vụ."""

    list_display = ("ma_bang_gia", "loai_xe", "loai_ap_dung", "gia_co_ban", "don_vi_thoi_gian_phut", "gia_tang_them", "gia_ban_dem", "ngay_ap_dung")
    list_filter = ("loai_xe", "loai_ap_dung")


@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    """Cấu hình trang quản trị Admin cho danh sách Vị trí đỗ xe."""

    list_display = ("ma_vi_tri", "code", "khu_vuc", "status")
    list_filter = ("khu_vuc", "status")
    search_fields = ("code",)

