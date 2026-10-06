"""Tests for manager account administration actions."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import NguoiDung, VaiTro


class UserAdministrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        manager_role = VaiTro.objects.create(ten_vai_tro="QuanLy")
        staff_role = VaiTro.objects.create(ten_vai_tro="NhanVien")
        self.manager = NguoiDung.objects.create(
            ten_dang_nhap="manager", ho_ten="Manager", vai_tro=manager_role
        )
        self.manager.set_password("manager123")
        self.manager.save()
        self.staff = NguoiDung.objects.create(
            ten_dang_nhap="staff", ho_ten="Staff", vai_tro=staff_role
        )
        self.staff.set_password("oldpass")
        self.staff.save()

        session = self.client.session
        session["user_id"] = self.manager.ma_nguoi_dung
        session["role"] = "QuanLy"
        session.save()

    def test_manager_can_reset_staff_password(self):
        response = self.client.post(
            f"/api/users/{self.staff.ma_nguoi_dung}/reset-password/",
            {"new_password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password("newpass123"))

    def test_manager_can_soft_delete_staff_account(self):
        response = self.client.delete(f"/api/users/{self.staff.ma_nguoi_dung}/")
        self.assertEqual(response.status_code, 200)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.trang_thai, "Nghỉ việc")
        self.assertFalse(self.staff.check_password("oldpass"))
        self.assertNotContains(self.client.get("/api/users/"), '"staff"')

    def test_manager_cannot_delete_own_account(self):
        response = self.client.delete(f"/api/users/{self.manager.ma_nguoi_dung}/")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_user_cannot_manage_accounts(self):
        self.client.session.flush()
        response = self.client.post(
            f"/api/users/{self.staff.ma_nguoi_dung}/reset-password/",
            {"new_password": "newpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
