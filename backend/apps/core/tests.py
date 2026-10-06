"""Bộ unit test cho các tính năng lõi bao gồm health check và trang chủ dashboard."""

from django.test import TestCase


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

