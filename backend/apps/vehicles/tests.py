"""Unit tests kiểm tra ràng buộc duy nhất và tạo mới cho mô hình Loại xe."""

from django.test import TestCase
from apps.vehicles.models import LoaiXe


class VehicleTypeTests(TestCase):
    """Bộ kiểm thử cho mô hình Loại xe (LoaiXe)."""

    def test_vehicle_type_unique(self):
        """Kiểm tra tên loại xe là duy nhất trong CSDL."""
        LoaiXe.objects.create(ten_loai_xe="OtoTest", mo_ta="Ô tô test")
        self.assertEqual(LoaiXe.objects.filter(ten_loai_xe="OtoTest").count(), 1)

