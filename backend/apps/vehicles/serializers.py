"""Serializers dữ liệu cho danh mục Loại xe và Phương tiện."""

from rest_framework import serializers
from apps.vehicles.models import LoaiXe, PhuongTien


class LoaiXeSerializer(serializers.ModelSerializer):
    """Serializer dữ liệu cho mô hình Loại xe."""

    class Meta:
        model = LoaiXe
        fields = ["ma_loai_xe", "ten_loai_xe", "mo_ta"]


class PhuongTienSerializer(serializers.ModelSerializer):
    """Serializer dữ liệu cho mô hình Phương tiện kèm chi tiết Loại xe."""

    ten_loai_xe = serializers.CharField(source="loai_xe.ten_loai_xe", read_only=True)
    loai_xe_detail = LoaiXeSerializer(source="loai_xe", read_only=True)

    class Meta:
        model = PhuongTien
        fields = ["ma_phuong_tien", "bien_so_xe", "loai_xe", "ten_loai_xe", "loai_xe_detail", "mau_xe", "mo_ta"]

