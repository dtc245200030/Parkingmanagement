"""Serializers chuyển đổi dữ liệu cho Vai trò và Người dùng/Nhân viên."""

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from apps.users.models import NguoiDung, VaiTro


class VaiTroSerializer(serializers.ModelSerializer):
    """Serializer dữ liệu cho vai trò người dùng."""

    class Meta:
        model = VaiTro
        fields = ["ma_vai_tro", "ten_vai_tro", "mo_ta"]


class NguoiDungSerializer(serializers.ModelSerializer):
    """Serializer hiển thị thông tin tài khoản người dùng và vai trò đi kèm."""

    vai_tro_detail = VaiTroSerializer(source="vai_tro", read_only=True)
    ten_vai_tro = serializers.CharField(source="vai_tro.ten_vai_tro", read_only=True)
    is_online = serializers.SerializerMethodField()

    def get_is_online(self, obj):
        """A user is online while their authenticated session is sending heartbeats."""
        return bool(obj.last_seen_at and obj.last_seen_at >= timezone.now() - timedelta(minutes=2))

    class Meta:
        model = NguoiDung
        fields = [
            "ma_nguoi_dung",
            "ten_dang_nhap",
            "ho_ten",
            "so_dien_thoai",
            "email",
            "vai_tro",
            "vai_tro_detail",
            "ten_vai_tro",
            "trang_thai",
            "ca_lam_viec",
            "ngay_tao",
            "is_online",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer xử lý tạo mới tài khoản người dùng với mật khẩu đã hash."""

    mat_khau = serializers.CharField(write_only=True, required=True, min_length=4)
    vai_tro_id = serializers.IntegerField(required=False, write_only=True)
    vai_tro_ten = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = NguoiDung
        fields = [
            "ma_nguoi_dung",
            "ten_dang_nhap",
            "mat_khau",
            "ho_ten",
            "so_dien_thoai",
            "email",
            "ca_lam_viec",
            "vai_tro_id",
            "vai_tro_ten",
        ]

    def create(self, validated_data):
        """Khởi tạo và lưu đối tượng NguoiDung mới kèm vai trò tương ứng."""
        raw_password = validated_data.pop("mat_khau")
        vai_tro_id = validated_data.pop("vai_tro_id", None)
        vai_tro_ten = validated_data.pop("vai_tro_ten", None)

        if vai_tro_id:
            vai_tro = VaiTro.objects.filter(pk=vai_tro_id).first()
        elif vai_tro_ten:
            vai_tro = VaiTro.objects.filter(ten_vai_tro__iexact=vai_tro_ten).first()
        else:
            vai_tro = VaiTro.objects.filter(ten_vai_tro="NhanVien").first() or VaiTro.objects.first()

        user = NguoiDung(**validated_data)
        user.vai_tro = vai_tro
        user.set_password(raw_password)
        user.save()
        return user
