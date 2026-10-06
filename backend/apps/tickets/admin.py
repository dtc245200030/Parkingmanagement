"""Cấu hình trang quản trị Admin cho Vé xe, Lượt gửi xe và Vé tháng."""

from django.contrib import admin
from apps.tickets.models import LuotGuiXe, VeThang, VeXe


@admin.register(VeXe)
class VeXeAdmin(admin.ModelAdmin):
    """Cấu hình trang quản trị Admin cho Thẻ/Vé xe RFID."""

    list_display = ("ma_ve", "ma_dinh_danh_the", "loai_the", "trang_thai_the")
    list_filter = ("loai_the", "trang_thai_the")
    search_fields = ("ma_dinh_danh_the",)


@admin.register(LuotGuiXe)
class LuotGuiXeAdmin(admin.ModelAdmin):
    """Cấu hình trang quản trị Admin cho Lượt gửi xe."""

    list_display = ("ma_luot_gui", "bien_so_xe_kiem_tra", "loai_xe", "khu_vuc", "thoi_gian_vao", "thoi_gian_ra", "tong_tien_phi", "trang_thai_luot")
    list_filter = ("trang_thai_luot", "khu_vuc", "loai_xe")
    search_fields = ("bien_so_xe_kiem_tra",)


@admin.register(VeThang)
class VeThangAdmin(admin.ModelAdmin):
    """Cấu hình trang quản trị Admin cho danh sách Vé tháng."""

    list_display = ("ma_ve_thang", "ho_ten_khach_hang", "phuong_tien", "so_dien_thoai", "ngay_bat_dau", "ngay_ket_thuc", "trang_thai_ve")
    list_filter = ("trang_thai_ve",)
    search_fields = ("ho_ten_khach_hang", "so_dien_thoai", "phuong_tien__bien_so_xe")

