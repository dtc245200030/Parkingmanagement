"""Bộ unit test cho luồng xe vào, xe ra, kiểm tra trùng lặp biển số và gia hạn vé tháng."""

from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.parking.models import KhuVuc
from apps.tickets.models import LuotGuiXe, VeThang
from apps.tickets.services import check_in_vehicle, check_out_vehicle
from apps.vehicles.models import LoaiXe, PhuongTien


class TicketsFlowTests(TestCase):
    """Bộ kiểm thử các luồng nghiệp vụ vé xe và lượt xe."""

    def setUp(self):
        """Khởi tạo dữ liệu mẫu cho Loại xe và Khu vực."""
        self.loai_xe = LoaiXe.objects.create(ten_loai_xe="XeMay", mo_ta="Xe may")
        KhuVuc.objects.create(ten_khu_vuc="Khu A", suc_chua_toi_da=120)
        self.khu_vuc = KhuVuc.objects.create(ten_khu_vuc="Khu B", suc_chua_toi_da=120)
        KhuVuc.objects.create(ten_khu_vuc="Khu C", suc_chua_toi_da=120)

    def test_check_in_vehicle_creates_active_session(self):
        """Kiểm tra quy trình check-in tạo thành công lượt xe trạng thái 'Đang gửi'."""
        session = check_in_vehicle(plate_number="29A-99999", vehicle_type_name="XeMay", zone_name="Khu B")
        self.assertEqual(session.trang_thai_luot, "Đang gửi")
        self.assertEqual(session.bien_so_xe_kiem_tra, "29A-99999")
        self.assertEqual(session.khu_vuc.ten_khu_vuc, "Khu B")

    def test_vehicle_types_are_assigned_to_three_fixed_zones(self):
        """Ô tô vào A, xe máy vào B và xe đạp vào C dù phía gửi lên chọn sai khu."""
        LoaiXe.objects.create(ten_loai_xe="Oto", mo_ta="O to")
        LoaiXe.objects.create(ten_loai_xe="XeDap", mo_ta="Xe dap")

        car = check_in_vehicle("30A-10001", "Oto", "Khu D")
        motorbike = check_in_vehicle("29A-10002", "XeMay", "Khu A")
        bicycle = check_in_vehicle("XD-10003", "XeDap", "Khu B")

        self.assertEqual(car.khu_vuc.ten_khu_vuc, "Khu A")
        self.assertEqual(motorbike.khu_vuc.ten_khu_vuc, "Khu B")
        self.assertEqual(bicycle.khu_vuc.ten_khu_vuc, "Khu C")

    def test_cannot_check_in_duplicate_plate(self):
        """Kiểm tra không thể check-in lại cho xe đang gửi trong bãi."""
        check_in_vehicle(plate_number="29A-99999", vehicle_type_name="XeMay", zone_name="Khu B")
        with self.assertRaises(ValueError):
            check_in_vehicle(plate_number="29A-99999", vehicle_type_name="XeMay", zone_name="Khu B")

    def test_check_out_vehicle(self):
        """Kiểm tra quy trình check-out cho xe ra bãi và chuyển trạng thái 'Đã ra'."""
        session = check_in_vehicle(plate_number="29A-88888", vehicle_type_name="XeMay", zone_name="Khu B")
        out_session = check_out_vehicle(session.ma_luot_gui)
        self.assertEqual(out_session.trang_thai_luot, "Đã ra")
        self.assertIsNotNone(out_session.thoi_gian_ra)

    def test_monthly_ticket_is_detected_at_check_in_and_free_at_check_out(self):
        """Xe có vé tháng hợp lệ được ghi nhận lúc vào và miễn phí lúc ra."""
        vehicle = PhuongTien.objects.create(bien_so_xe="30A-33333", loai_xe=self.loai_xe)
        monthly_ticket = VeThang.objects.create(
            phuong_tien=vehicle,
            ho_ten_khach_hang="Nguyen Van C",
            ngay_bat_dau=date.today(),
            ngay_ket_thuc=date.today() + timedelta(days=30),
            trang_thai_ve="Còn hiệu lực",
        )

        session = check_in_vehicle(plate_number="30A-33333", vehicle_type_name="XeMay", zone_name="Khu B")
        self.assertTrue(session.la_ve_thang)
        self.assertEqual(session.ve_thang, monthly_ticket)

        out_session = check_out_vehicle(session.ma_luot_gui)
        self.assertEqual(out_session.tong_tien_phi, Decimal("0.00"))

    def test_staff_can_renew_monthly_ticket(self):
        """Nhân viên được phép gia hạn vé tháng."""
        client = APIClient()
        session = client.session
        session["user_id"] = 2
        session["role"] = "NhanVien"
        session.save()
        pt = PhuongTien.objects.create(bien_so_xe="30A-11111", loai_xe=self.loai_xe)
        vt = VeThang.objects.create(
            phuong_tien=pt,
            ho_ten_khach_hang="Nguyen Van A",
            ngay_bat_dau=date.today(),
            ngay_ket_thuc=date.today() + timedelta(days=30),
            trang_thai_ve="Còn hiệu lực"
        )
        response = client.post(f"/api/tickets/monthly/{vt.ma_ve_thang}/renew/", {"months": 1}, format="json")
        self.assertEqual(response.status_code, 200)
        vt.refresh_from_db()
        self.assertEqual(vt.ngay_ket_thuc, date.today() + timedelta(days=60))

    def test_manager_cannot_delete_monthly_ticket(self):
        """Quản lý không được phép xóa vé tháng."""
        client = APIClient()
        session = client.session
        session["user_id"] = 1
        session["role"] = "QuanLy"
        session.save()
        pt = PhuongTien.objects.create(bien_so_xe="30A-22222", loai_xe=self.loai_xe)
        vt = VeThang.objects.create(
            phuong_tien=pt,
            ho_ten_khach_hang="Nguyen Van B",
            ngay_bat_dau=date.today(),
            ngay_ket_thuc=date.today() + timedelta(days=30),
            trang_thai_ve="Còn hiệu lực"
        )
        response = client.delete(f"/api/tickets/monthly/{vt.ma_ve_thang}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(VeThang.objects.filter(pk=vt.ma_ve_thang).exists())
