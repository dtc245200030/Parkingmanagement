"""Mô hình dữ liệu cho Vai trò (VaiTro) và Người dùng/Nhân viên (NguoiDung)."""

from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class VaiTro(models.Model):
    """Model định nghĩa các vai trò trong hệ thống (QuanLy, NhanVien)."""

    ma_vai_tro = models.BigAutoField(primary_key=True)
    ten_vai_tro = models.CharField(max_length=50, unique=True, verbose_name="Tên vai trò")
    mo_ta = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mô tả")

    class Meta:
        db_table = "VaiTro"
        verbose_name = "Vai trò"
        verbose_name_plural = "Danh mục Vai trò"

    def __str__(self):
        """Mô tả chuỗi đại diện cho vai trò."""
        return self.ten_vai_tro


class NguoiDung(models.Model):
    """Model quản lý thông tin tài khoản nhân viên và người quản lý bãi đỗ xe."""

    class TrangThaiChoices(models.TextChoices):
        HOAT_DONG = "Hoạt động", "Hoạt động"
        KHOA = "Khóa", "Khóa"
        TAM_NGHI = "Tạm nghỉ", "Tạm nghỉ"

    ma_nguoi_dung = models.BigAutoField(primary_key=True)
    ten_dang_nhap = models.CharField(max_length=50, unique=True, verbose_name="Tên đăng nhập")
    mat_khau = models.CharField(max_length=255, verbose_name="Mật khẩu (Hash)")
    ho_ten = models.CharField(max_length=100, verbose_name="Họ và tên")
    so_dien_thoai = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    vai_tro = models.ForeignKey(VaiTro, on_delete=models.PROTECT, related_name="nguoi_dung_list", verbose_name="Vai trò")
    trang_thai = models.CharField(
        max_length=20,
        choices=TrangThaiChoices.choices,
        default=TrangThaiChoices.HOAT_DONG,
        verbose_name="Trạng thái"
    )
    ca_lam_viec = models.CharField(
        max_length=100,
        default="Ca hành chính (8h–17h) • Tất cả khu",
        verbose_name="Ca làm việc"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    ngay_tao = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    last_seen_at = models.DateTimeField(null=True, blank=True, verbose_name="Hoạt động gần nhất")

    class Meta:
        db_table = "NguoiDung"
        verbose_name = "Người dùng"
        verbose_name_plural = "Danh sách Người dùng"

    def __str__(self):
        """Mô tả chuỗi đại diện cho người dùng."""
        return f"{self.ho_ten} ({self.ten_dang_nhap})"

    def set_password(self, raw_password):
        """Mã hóa mật khẩu dạng thô thành chuỗi hash an toàn."""
        self.mat_khau = make_password(raw_password)

    def check_password(self, raw_password):
        """Xác thực mật khẩu dạng thô khớp với mật khẩu hash trong CSDL."""
        return check_password(raw_password, self.mat_khau)
