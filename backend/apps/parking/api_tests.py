"""Các unit test kiểm tra phân quyền API và các thao tác CRUD danh mục xe."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class CrudPermissionTests(TestCase):
    """Bộ kiểm thử phân quyền các API CRUD."""

    def setUp(self):
        """Khởi tạo tài khoản test (nhân viên và admin)."""
        self.client = APIClient()
        self.staff = get_user_model().objects.create_user(username="staff", password="secret")
        self.admin = get_user_model().objects.create_superuser(username="admin", password="secret", email="admin@example.com")

    def test_create_vehicle_type(self):
        """Kiểm tra gọi API tạo loại xe mới qua endpoint /api/vehicle-types/."""
        response = self.client.post("/api/vehicle-types/", {"ten_loai_xe": "XeMoi"}, format="json")
        self.assertEqual(response.status_code, 201)

