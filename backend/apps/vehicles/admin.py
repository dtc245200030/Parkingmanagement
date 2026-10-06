"""Cấu hình trang quản trị Admin cho danh mục Loại xe và Phương tiện."""

from django.contrib import admin
from apps.vehicles.models import LoaiXe, PhuongTien


@admin.register(LoaiXe)
class LoaiXeAdmin(admin.ModelAdmin):
    """Cấu hình trang Admin cho mô hình Loại xe."""

    list_display = ("ma_loai_xe", "ten_loai_xe", "mo_ta")
    search_fields = ("ten_loai_xe",)


@admin.register(PhuongTien)
class PhuongTienAdmin(admin.ModelAdmin):
    """Cấu hình trang Admin cho mô hình Phương tiện."""

    list_display = ("ma_phuong_tien", "bien_so_xe", "loai_xe", "mau_xe", "mo_ta")
    list_filter = ("loai_xe",)
    search_fields = ("bien_so_xe", "mau_xe")

