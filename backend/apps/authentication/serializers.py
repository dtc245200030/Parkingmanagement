"""Serializer dữ liệu cho các thao tác đăng nhập và đăng ký tài khoản."""

from rest_framework import serializers
from apps.users.models import NguoiDung, VaiTro


class LoginSerializer(serializers.Serializer):
    """Serializer xác thực thông tin đăng nhập gồm username và password."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class RegisterAccountSerializer(serializers.ModelSerializer):
    """Serializer cho phép đăng ký tài khoản người dùng mới vào hệ thống."""

    password = serializers.CharField(write_only=True, required=True, min_length=4)
    role_name = serializers.CharField(required=False, default="Nhân viên")

    class Meta:
        model = NguoiDung
        fields = [
            "ma_nguoi_dung",
            "ten_dang_nhap",
            "password",
            "ho_ten",
            "so_dien_thoai",
            "email",
            "role_name",
        ]

    def create(self, validated_data):
        """Tạo đối tượng NguoiDung mới với mật khẩu đã được mã hóa (hash)."""
        password = validated_data.pop("password")
        role_name = validated_data.pop("role_name", "Nhân viên")

        vai_tro = VaiTro.objects.filter(ten_vai_tro__iexact=role_name).first()
        if not vai_tro:
            vai_tro = VaiTro.objects.first()

        user = NguoiDung(
            ten_dang_nhap=validated_data.get("ten_dang_nhap"),
            ho_ten=validated_data.get("ho_ten"),
            so_dien_thoai=validated_data.get("so_dien_thoai", ""),
            email=validated_data.get("email", ""),
            vai_tro=vai_tro,
        )
        user.set_password(password)
        user.save()
        return user

