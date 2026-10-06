"""Các unit test kiểm tra tính năng đăng nhập, đăng xuất và phân quyền cho module authentication."""

from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import NguoiDung, VaiTro


class AuthenticationTests(TestCase):
    """Bộ kiểm thử tính năng đăng nhập, lấy thông tin cá nhân và đăng xuất."""

    def setUp(self):
        """Khởi tạo dữ liệu mẫu cho kiểm thử đăng nhập."""
        self.client = APIClient()
        vt = VaiTro.objects.create(ten_vai_tro="NhanVien", mo_ta="Nhan vien")
        self.user = NguoiDung.objects.create(ten_dang_nhap="staff", ho_ten="Staff", vai_tro=vt)
        self.user.set_password("secret")
        self.user.save()

    def test_login_me_logout(self):
        """Kiểm tra luồng đăng nhập thành công, gọi API /me/ và đăng xuất."""
        response = self.client.post("/api/auth/login/", {"username": "staff", "password": "secret"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_seen_at)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.last_seen_at)

    def test_invalid_login_does_not_reveal_credentials(self):
        """Kiểm tra đăng nhập sai mật khẩu trả về HTTP 401 và không làm lộ thông tin mật khẩu."""
        response = self.client.post("/api/auth/login/", {"username": "staff", "password": "wrong_password_xyz"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("wrong_password_xyz", response.content.decode())
