"""Mô hình dữ liệu lưu trữ báo cáo thống kê lượt xe và doanh thu (BaoCaoThongKe)."""

from django.db import models
from apps.parking.models import KhuVuc


class BaoCaoThongKe(models.Model):
    """Model tổng hợp báo cáo định kỳ theo ngày, tuần, tháng cho bãi đỗ xe."""

    class LoaiBaoCao(models.TextChoices):
        NGAY = "Ngay", "Theo ngày"
        TUAN = "Tuan", "Theo tuần"
        THANG = "Thang", "Theo tháng"

    ma_bao_cao = models.BigAutoField(primary_key=True)
    loai_bao_cao = models.CharField(max_length=20, choices=LoaiBaoCao.choices, verbose_name="Loại báo cáo")
    ngay_bat_dau = models.DateField(verbose_name="Ngày bắt đầu")
    ngay_ket_thuc = models.DateField(verbose_name="Ngày kết thúc")
    khu_vuc = models.ForeignKey(KhuVuc, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Khu vực")
    tong_luot_xe = models.IntegerField(default=0, verbose_name="Tổng lượt xe")
    tong_doanh_thu = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="Tổng doanh thu (VNĐ)")
    ty_le_lap_day_trung_binh = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Tỷ lệ lấp đầy (%)")
    khung_gio_cao_diem = models.CharField(max_length=255, blank=True, null=True, verbose_name="Khung giờ cao điểm")
    ngay_tao = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm tổng hợp")

    class Meta:
        db_table = "BaoCaoThongKe"
        verbose_name = "Báo cáo thống kê"
        verbose_name_plural = "Dữ liệu Báo cáo & Thống kê"

    def __str__(self):
        """Mô tả chuỗi đại diện cho bản ghi báo cáo."""
        return f"Báo cáo {self.get_loai_bao_cao_display()} ({self.ngay_bat_dau} -> {self.ngay_ket_thuc})"

