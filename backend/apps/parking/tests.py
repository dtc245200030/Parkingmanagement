"""Các unit test kiểm tra việc tạo dữ liệu Model Khu vực đỗ xe và Bảng giá."""

from decimal import Decimal
from django.test import TestCase
from apps.parking.models import KhuVuc, BangGia
from apps.vehicles.models import LoaiXe


class ParkingModelTests(TestCase):
    """Bộ kiểm thử cho Data Models trong app parking."""

    def setUp(self):
        """Khởi tạo dữ liệu mẫu Loại xe để kiểm thử Bảng giá."""
        self.loai_xe = LoaiXe.objects.create(ten_loai_xe="XeMay", mo_ta="Xe may")

    def test_create_khu_vuc(self):
        """Kiểm tra tạo thành công đối tượng KhuVuc."""
        zone = KhuVuc.objects.create(ten_khu_vuc="Khu A", suc_chua_toi_da=120)
        self.assertEqual(zone.suc_chua_toi_da, 120)

    def test_create_bang_gia(self):
        """Kiểm tra tạo thành công đối tượng BangGia cho vé lượt."""
        bg = BangGia.objects.create(
            loai_xe=self.loai_xe,
            loai_ap_dung="VeLuot",
            gia_co_ban=Decimal("5000"),
            don_vi_thoi_gian_phut=60
        )
        self.assertEqual(bg.gia_co_ban, Decimal("5000"))

