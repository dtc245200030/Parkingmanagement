"""Bộ unit test cho luồng xe vào, xe ra, kiểm tra trùng lặp biển số và gia hạn vé tháng."""

from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.parking.models import KhuVuc
from apps.tickets.models import LuotGuiXe, VeThang, VeXe
from apps.tickets.services import check_in_vehicle, check_out_vehicle
from apps.vehicles.models import LoaiXe, PhuongTien


class TicketsFlowTests(TestCase):
    """Bộ kiểm thử các luồng nghiệp vụ vé xe và lượt xe."""

    def setUp(self):
        """Khởi tạo dữ liệu mẫu cho Loại xe và Khu vực."""
        self.loai_xe = LoaiXe.objects.create(ten_loai_xe="XeMay", mo_ta="Xe may")
        self.khu_vuc = KhuVuc.objects.create(ten_khu_vuc="Khu A", suc_chua_toi_da=120)

    def test_check_in_vehicle_creates_active_session(self):
        """Kiểm tra quy trình check-in tạo thành công lượt xe trạng thái 'Đang gửi'."""
        session = check_in_vehicle(plate_number="29A-99999", vehicle_type_name="XeMay", zone_name="Khu A")
        self.assertEqual(session.trang_thai_luot, "Đang gửi")
        self.assertEqual(session.bien_so_xe_kiem_tra, "29A-99999")
        self.assertEqual(session.khu_vuc.ten_khu_vuc, "Khu A")

    def test_cannot_check_in_duplicate_plate(self):
        """Kiểm tra không thể check-in lại cho xe đang gửi trong bãi."""
        check_in_vehicle(plate_number="29A-99999", vehicle_type_name="XeMay", zone_name="Khu A")
        with self.assertRaises(ValueError):
            check_in_vehicle(plate_number="29A-99999", vehicle_type_name="XeMay", zone_name="Khu A")

    def test_check_out_vehicle(self):
        """Kiểm tra quy trình check-out cho xe ra bãi và chuyển trạng thái 'Đã ra'."""
        session = check_in_vehicle(plate_number="29A-88888", vehicle_type_name="XeMay", zone_name="Khu A")
        out_session = check_out_vehicle(session.ma_luot_gui)
        self.assertEqual(out_session.trang_thai_luot, "Đã ra")
        self.assertIsNotNone(out_session.thoi_gian_ra)

    def test_renew_monthly_ticket(self):
        """Kiểm tra API gia hạn thời hạn vé tháng."""
        client = APIClient()
        pt = PhuongTien.objects.create(bien_so_xe="30A-11111", loai_xe=self.loai_xe)
        card = VeXe.objects.create(ma_dinh_danh_the="CARD-THANG-30A11111", loai_the="Vé tháng")
        vt = VeThang.objects.create(
            the_xe=card,
            phuong_tien=pt,
            ho_ten_khach_hang="Nguyen Van A",
            ngay_bat_dau=date.today(),
            ngay_ket_thuc=date.today() + timedelta(days=30),
            trang_thai_ve="Còn hiệu lực"
        )
        response = client.post(f"/api/tickets/monthly/{vt.ma_ve_thang}/renew/", {"months": 1}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_delete_monthly_ticket(self):
        """Kiểm tra API xóa vé tháng thành công."""
        client = APIClient()
        pt = PhuongTien.objects.create(bien_so_xe="30A-22222", loai_xe=self.loai_xe)
        card = VeXe.objects.create(ma_dinh_danh_the="CARD-THANG-30A22222", loai_the="Vé tháng")
        vt = VeThang.objects.create(
            the_xe=card,
            phuong_tien=pt,
            ho_ten_khach_hang="Nguyen Van B",
            ngay_bat_dau=date.today(),
            ngay_ket_thuc=date.today() + timedelta(days=30),
            trang_thai_ve="Còn hiệu lực"
        )
        response = client.delete(f"/api/tickets/monthly/{vt.ma_ve_thang}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(VeThang.objects.filter(pk=vt.ma_ve_thang).exists())

