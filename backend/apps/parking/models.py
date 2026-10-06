"""Định nghĩa các Data Models cho khu vực đỗ xe (KhuVuc), bảng giá (BangGia) và vị trí đỗ (ParkingSpot)."""

from django.core.validators import MinValueValidator
from django.db import models
from apps.vehicles.models import LoaiXe


class KhuVuc(models.Model):
    """Model đại diện cho một Khu vực đỗ xe (Ví dụ: Khu A, Khu B)."""

    ma_khu_vuc = models.BigAutoField(primary_key=True)
    ten_khu_vuc = models.CharField(max_length=20, unique=True, verbose_name="Tên khu vực")
    suc_chua_toi_da = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Sức chứa tối đa")
    mo_ta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "KhuVuc"
        verbose_name = "Khu vực đỗ xe"
        verbose_name_plural = "Danh mục Khu vực đỗ xe"

    def __str__(self):
        """Mô tả chuỗi đại diện cho khu vực đỗ xe."""
        return f"{self.ten_khu_vuc} ({self.suc_chua_toi_da} chỗ)"


class BangGia(models.Model):
    """Model quy định cấu hình bảng giá gửi xe theo loại xe và thời gian."""

    class LoaiApDung(models.TextChoices):
        VE_LUOT = "VeLuot", "Vé lượt"
        VE_THANG = "VeThang", "Vé tháng"

    ma_bang_gia = models.BigAutoField(primary_key=True)
    loai_xe = models.ForeignKey(LoaiXe, on_delete=models.CASCADE, related_name="bang_gia_list", verbose_name="Loại xe")
    loai_ap_dung = models.CharField(max_length=20, choices=LoaiApDung.choices, default=LoaiApDung.VE_LUOT, verbose_name="Loại áp dụng")
    gia_co_ban = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Giá cơ bản (VNĐ)")
    don_vi_thoi_gian_phut = models.IntegerField(default=60, verbose_name="Đơn vị tính (phút)")
    gia_tang_them = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Giá tăng thêm mỗi chu kỳ (VNĐ)")
    gia_ban_dem = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Phụ phí ban đêm (VNĐ)")
    ngay_ap_dung = models.DateTimeField(auto_now_add=True, verbose_name="Ngày áp dụng")

    class Meta:
        db_table = "BangGia"
        verbose_name = "Bảng giá"
        verbose_name_plural = "Bảng giá tính phí"

    def __str__(self):
        """Mô tả chuỗi đại diện cho quy tắc bảng giá."""
        return f"{self.loai_xe.ten_loai_xe} - {self.get_loai_ap_dung_display()}: {self.gia_co_ban:,.0f} đ"


class ParkingSpot(models.Model):
    """Model đại diện cho từng vị trí đỗ xe cụ thể trong bãi đỗ."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Trống"
        OCCUPIED = "occupied", "Đang đỗ"
        MAINTENANCE = "maintenance", "Bảo trì"

    ma_vi_tri = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=40, unique=True, verbose_name="Mã vị trí")
    khu_vuc = models.ForeignKey(KhuVuc, on_delete=models.CASCADE, related_name="spots", verbose_name="Khu vực", null=True, blank=True)
    area = models.CharField(max_length=80, blank=True, verbose_name="Khu vực (text)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name="Trạng thái")

    class Meta:
        db_table = "ViTriDo"
        verbose_name = "Vị trí đỗ xe"
        verbose_name_plural = "Danh sách Vị trí đỗ xe"

    def __str__(self):
        """Mô tả chuỗi đại diện cho vị trí đỗ xe."""
        return f"{self.code} ({self.get_status_display()})"


# Backward compatibility aliases
PricingRule = BangGia

