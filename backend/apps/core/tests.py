"""Bộ unit test cho các tính năng lõi bao gồm health check và trang chủ dashboard."""

from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from apps.users.models import NguoiDung, VaiTro


class CoreTests(TestCase):
    """Kiểm tra các endpoint cơ bản của ứng dụng lõi."""

    def test_health_endpoint(self):
        """Kiểm tra endpoint /health/ trả về trạng thái HTTP 200 OK."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_dashboard_endpoint(self):
        """Kiểm tra trang chủ dashboard hoạt động và phản hồi HTML chứa ParkAI."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ParkAI")

    def test_dashboard_has_all_main_function_sections(self):
        """Kiểm tra trang dashboard hiển thị đầy đủ các mục chức năng chính."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        for label in [
            "Tổng quan",
            "Xe vào / Ra",
            "Tra cứu",
            "Vé tháng",
            "Thống kê",
            "Trợ lý AI",
            "Nhân viên",
            "Cài đặt",
        ]:
            self.assertContains(response, label)

    def test_backup_api_rejects_unauthenticated_user(self):
        response = self.client.get("/api/system/backups/")
        self.assertEqual(response.status_code, 403)

    @patch("apps.core.views.create_backup", return_value=Path("parkai_backup_20261026_120000_1234abcd.sqlite3"))
    def test_manager_can_create_backup(self, mocked_create):
        role = VaiTro.objects.create(ten_vai_tro="QuanLy")
        manager = NguoiDung.objects.create(
            ten_dang_nhap="backup_manager",
            mat_khau="unused",
            ho_ten="Quan ly sao luu",
            vai_tro=role,
        )
        session = self.client.session
        session["user_id"] = manager.ma_nguoi_dung
        session["role"] = "QuanLy"
        session.save()

        response = self.client.post("/api/system/backups/create/")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "success")
        mocked_create.assert_called_once_with()

