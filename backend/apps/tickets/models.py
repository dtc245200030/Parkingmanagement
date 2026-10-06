"""Mô hình dữ liệu cho Thẻ/Vé xe (VeXe), Lượt gửi xe (LuotGuiXe) và Vé tháng (VeThang)."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.parking.models import KhuVuc, ParkingSpot
from apps.users.models import NguoiDung
from apps.vehicles.models import LoaiXe, PhuongTien


class VeXe(models.Model):
    """Model quản lý thẻ giữ xe RFID hoặc vé giấy trong hệ thống bãi đỗ."""

    class LoaiThe(models.TextChoices):
        VE_LUOT = "Vé lượt", "Vé lượt"
        VE_THANG = "Vé tháng", "Vé tháng"

    class TrangThaiThe(models.TextChoices):
        SAN_SANG = "Sẵn sàng", "Sẵn sàng"
        DANG_GUI = "Đang gửi", "Đang gửi"
        KHOA = "Khóa", "Khóa"
        HONG = "Hỏng", "Hỏng"

    ma_ve = models.BigAutoField(primary_key=True)
    ma_dinh_danh_the = models.CharField(max_length=50, unique=True, verbose_name="Mã định danh thẻ (RFID)")
    loai_the = models.CharField(max_length=20, choices=LoaiThe.choices, default=LoaiThe.VE_LUOT, verbose_name="Loại thẻ")
    trang_thai_the = models.CharField(max_length=20, choices=TrangThaiThe.choices, default=TrangThaiThe.SAN_SANG, verbose_name="Trạng thái thẻ")

    class Meta:
        db_table = "VeXe"
        verbose_name = "Vé xe"
        verbose_name_plural = "Danh mục Vé xe"

    def __str__(self):
        """Mô tả chuỗi đại diện cho vé xe."""
        return f"{self.ma_dinh_danh_the} ({self.loai_the} - {self.trang_thai_the})"


class LuotGuiXe(models.Model):
    """Model ghi nhận chi tiết lượt gửi xe vào và ra khỏi bãi."""

    class TrangThaiLuot(models.TextChoices):
        DANG_GUI = "Đang gửi", "Đang gửi"
        DA_RA = "Đã ra", "Đã ra"

    ma_luot_gui = models.BigAutoField(primary_key=True)
    ve_xe = models.ForeignKey(VeXe, on_delete=models.PROTECT, related_name="luot_gui_list", verbose_name="Vé xe")
    phuong_tien = models.ForeignKey(PhuongTien, on_delete=models.SET_NULL, null=True, blank=True, related_name="luot_gui_list", verbose_name="Phương tiện")
    bien_so_xe_kiem_tra = models.CharField(max_length=20, verbose_name="Biển số xe")
    loai_xe = models.ForeignKey(LoaiXe, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Loại xe")
    khu_vuc = models.ForeignKey(KhuVuc, on_delete=models.PROTECT, null=True, blank=True, related_name="luot_gui_list", verbose_name="Khu vực")
    vi_tri = models.ForeignKey(ParkingSpot, on_delete=models.SET_NULL, null=True, blank=True, related_name="luot_gui_list", verbose_name="Vị trí đỗ")
    thoi_gian_vao = models.DateTimeField(default=timezone.now, verbose_name="Thời gian vào")
    thoi_gian_ra = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian ra")
    nguoi_dung_vao = models.ForeignKey(NguoiDung, on_delete=models.PROTECT, related_name="luot_vao_list", verbose_name="Nhân viên ghi nhận vào", null=True, blank=True)
    nguoi_dung_ra = models.ForeignKey(NguoiDung, on_delete=models.PROTECT, related_name="luot_ra_list", verbose_name="Nhân viên ghi nhận ra", null=True, blank=True)
    tong_tien_phi = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, validators=[MinValueValidator(0)], verbose_name="Tổng tiền phí (VNĐ)")
    trang_thai_luot = models.CharField(max_length=20, choices=TrangThaiLuot.choices, default=TrangThaiLuot.DANG_GUI, verbose_name="Trạng thái lượt")

    class Meta:
        db_table = "LuotGuiXe"
        verbose_name = "Lượt gửi xe"
        verbose_name_plural = "Danh sách Lượt gửi xe"
        constraints = [
            models.CheckConstraint(
                check=models.Q(thoi_gian_ra__isnull=True) | models.Q(thoi_gian_ra__gte=models.F("thoi_gian_vao")),
                name="chk_thoi_gian_hop_le",
            )
        ]

    def __str__(self):
        """Mô tả chuỗi đại diện cho lượt gửi xe."""
        return f"{self.bien_so_xe_kiem_tra} - {self.thoi_gian_vao:%d/%m %H:%M} ({self.trang_thai_luot})"


class VeThang(models.Model):
    """Model quản lý thông tin khách hàng đăng ký vé tháng."""

    class TrangThaiVe(models.TextChoices):
        CON_HIEU_LUC = "Còn hiệu lực", "Còn hiệu lực"
        HET_HAN = "Đã hết hạn", "Đã hết hạn"
        SAP_HET_HAN = "Sắp hết hạn", "Sắp hết hạn"

    ma_ve_thang = models.BigAutoField(primary_key=True)
    the_xe = models.ForeignKey(VeXe, on_delete=models.PROTECT, related_name="ve_thang_list", verbose_name="Thẻ xe")
    phuong_tien = models.ForeignKey(PhuongTien, on_delete=models.CASCADE, related_name="ve_thang_list", verbose_name="Phương tiện")
    ho_ten_khach_hang = models.CharField(max_length=100, verbose_name="Họ tên khách hàng")
    so_dien_thoai = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    ngay_bat_dau = models.DateField(verbose_name="Ngày bắt đầu")
    ngay_ket_thuc = models.DateField(verbose_name="Ngày kết thúc")
    moi_gia_han = models.BooleanField(default=True, verbose_name="Mới gia hạn")
    trang_thai_ve = models.CharField(max_length=20, choices=TrangThaiVe.choices, default=TrangThaiVe.CON_HIEU_LUC, verbose_name="Trạng thái vé")

    class Meta:
        db_table = "VeThang"
        verbose_name = "Vé tháng"
        verbose_name_plural = "Danh sách Vé tháng"

    def __str__(self):
        """Mô tả chuỗi đại diện cho vé tháng."""
        return f"{self.ho_ten_khach_hang} - {self.phuong_tien.bien_so_xe} ({self.trang_thai_ve})"


# Backward compatibility aliases
ParkingTicket = VeXe
ParkingSession = LuotGuiXe

