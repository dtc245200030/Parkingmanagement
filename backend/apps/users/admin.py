"""Cấu hình trang quản trị Admin cho danh mục Vai trò và Người dùng."""

from django.contrib import admin
from apps.users.models import NguoiDung, VaiTro


@admin.register(VaiTro)
class VaiTroAdmin(admin.ModelAdmin):
    """Cấu hình giao diện Admin cho mô hình Vai trò."""

    list_display = ("ma_vai_tro", "ten_vai_tro", "mo_ta")
    search_fields = ("ten_vai_tro",)


@admin.register(NguoiDung)
class NguoiDungAdmin(admin.ModelAdmin):
    """Cấu hình giao diện Admin cho mô hình Người dùng."""

    list_display = ("ma_nguoi_dung", "ten_dang_nhap", "ho_ten", "so_dien_thoai", "vai_tro", "trang_thai", "ngay_tao")
    list_filter = ("vai_tro", "trang_thai")
    search_fields = ("ten_dang_nhap", "ho_ten", "so_dien_thoai")

