"""Views xử lý API xác thực người dùng bao gồm đăng nhập, đăng ký, đăng xuất và lấy thông tin cá nhân (me)."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone

from apps.authentication.serializers import LoginSerializer, RegisterAccountSerializer
from apps.users.models import NguoiDung, VaiTro
from apps.users.serializers import NguoiDungSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Xử lý đăng nhập tài khoản người dùng, kiểm tra mật khẩu đã mã hóa và lưu thông tin vào Session."""
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    # Check NguoiDung database table
    user = NguoiDung.objects.filter(ten_dang_nhap=username).select_related("vai_tro").first()
    if user is None:
        # Fallback check for case insensitive
        user = NguoiDung.objects.filter(ten_dang_nhap__iexact=username).select_related("vai_tro").first()

    # Chỉ chấp nhận mật khẩu đã hash trong CSDL, không còn mật khẩu cứng mặc định
    if user and user.check_password(password):
        if user.trang_thai != "Hoạt động":
            return Response(
                {"code": "ACCOUNT_DISABLED", "message": "Tài khoản đã bị khóa hoặc ngừng hoạt động."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Set session data
        request.session["user_id"] = user.ma_nguoi_dung
        request.session["username"] = user.ten_dang_nhap
        request.session["role"] = user.vai_tro.ten_vai_tro if user.vai_tro else "NhanVien"
        user.last_seen_at = timezone.now()
        user.save(update_fields=["last_seen_at"])

        return Response(
            {
                "status": "success",
                "message": "Đăng nhập thành công",
                "user": {
                    "id": user.ma_nguoi_dung,
                    "username": user.ten_dang_nhap,
                    "fullName": user.ho_ten,
                    "phone": user.so_dien_thoai,
                    "email": user.email,
                    "role": user.vai_tro.ten_vai_tro if user.vai_tro else "NhanVien",
                    "roleDesc": user.vai_tro.mo_ta if user.vai_tro else "",
                    "shift": user.ca_lam_viec,
                },
            }
        )

    return Response(
        {"code": "INVALID_CREDENTIALS", "message": "Tên đăng nhập hoặc mật khẩu không chính xác."},
        status=status.HTTP_401_UNAUTHORIZED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """Đăng ký tài khoản người dùng mới."""
    serializer = RegisterAccountSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "status": "success",
                "message": "Đăng ký tài khoản thành công!",
                "user": {
                    "id": user.ma_nguoi_dung,
                    "username": user.ten_dang_nhap,
                    "fullName": user.ho_ten,
                    "role": user.vai_tro.ten_vai_tro if user.vai_tro else "NhanVien",
                },
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"status": "error", "errors": serializer.errors, "message": "Thông tin đăng ký không hợp lệ."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    """Xóa thông tin phiên làm việc (Session) của người dùng hiện tại."""
    user_id = request.session.get("user_id")
    if user_id:
        NguoiDung.objects.filter(pk=user_id).update(last_seen_at=None)
    request.session.flush()
    return Response({"status": "logged_out", "message": "Đã đăng xuất"})


@api_view(["GET"])
@permission_classes([AllowAny])
def me_view(request):
    """Lấy thông tin tài khoản đang đăng nhập từ Session hiện tại."""
    user_id = request.session.get("user_id")
    if user_id:
        user = NguoiDung.objects.filter(pk=user_id).select_related("vai_tro").first()
        if user:
            user.last_seen_at = timezone.now()
            user.save(update_fields=["last_seen_at"])
            return Response(
                {
                    "authenticated": True,
                    "user": {
                        "id": user.ma_nguoi_dung,
                        "username": user.ten_dang_nhap,
                        "fullName": user.ho_ten,
                        "phone": user.so_dien_thoai,
                        "email": user.email,
                        "role": user.vai_tro.ten_vai_tro if user.vai_tro else "NhanVien",
                        "shift": user.ca_lam_viec,
                    },
                }
            )
    return Response({"authenticated": False, "user": None})
