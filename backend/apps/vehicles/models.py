"""Mô hình dữ liệu cho Danh mục Loại xe (LoaiXe) và Phương tiện (PhuongTien)."""

from django.db import models


class LoaiXe(models.Model):
    """Model định nghĩa các loại xe được chấp nhận trong bãi (Xe máy, Ô tô, Xe đạp,...)."""

    ma_loai_xe = models.BigAutoField(primary_key=True)
    ten_loai_xe = models.CharField(max_length=50, unique=True, verbose_name="Tên loại xe")
    mo_ta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "LoaiXe"
        verbose_name = "Loại xe"
        verbose_name_plural = "Danh mục Loại xe"

    def __str__(self):
        """Mô tả chuỗi đại diện cho loại xe."""
        return self.ten_loai_xe


class PhuongTien(models.Model):
    """Model đại diện cho từng phương tiện cụ thể dựa theo biển số xe."""

    ma_phuong_tien = models.BigAutoField(primary_key=True)
    bien_so_xe = models.CharField(max_length=20, verbose_name="Biển số xe")
    loai_xe = models.ForeignKey(LoaiXe, on_delete=models.CASCADE, related_name="phuong_tien_list", verbose_name="Loại xe")
    mau_xe = models.CharField(max_length=50, blank=True, null=True, verbose_name="Màu xe")
    mo_ta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "PhuongTien"
        verbose_name = "Phương tiện"
        verbose_name_plural = "Danh sách Phương tiện"

    def __str__(self):
        """Mô tả chuỗi đại diện cho phương tiện."""
        return f"{self.bien_so_xe} ({self.loai_xe.ten_loai_xe})"


# Backward compatibility aliases
VehicleType = LoaiXe

