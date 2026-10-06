"""Cấu hình giao diện Admin quản trị các bản ghi báo cáo thống kê."""

from django.contrib import admin
from apps.reports.models import BaoCaoThongKe


@admin.register(BaoCaoThongKe)
class BaoCaoThongKeAdmin(admin.ModelAdmin):
    """Cấu hình trang Admin cho mô hình Báo cáo Thống kê."""

    list_display = ("ma_bao_cao", "loai_bao_cao", "ngay_bat_dau", "ngay_ket_thuc", "khu_vuc", "tong_luot_xe", "tong_doanh_thu")
    list_filter = ("loai_bao_cao", "khu_vuc")

