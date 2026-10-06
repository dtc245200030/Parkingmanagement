"""ViewSets quản lý danh mục vai trò và thông tin tài khoản người dùng/nhân viên."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.models import NguoiDung, VaiTro
from apps.users.serializers import NguoiDungSerializer, RegisterSerializer, VaiTroSerializer


class VaiTroViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet chỉ đọc để truy vấn danh mục vai trò hệ thống."""

    queryset = VaiTro.objects.all()
    serializer_class = VaiTroSerializer
    permission_classes = [AllowAny]


class NguoiDungViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý CRUD danh sách tài khoản người dùng và đăng ký nhân viên mới."""

    queryset = NguoiDung.objects.exclude(trang_thai="Nghỉ việc").select_related("vai_tro").order_by("-ma_nguoi_dung")
    serializer_class = NguoiDungSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """Trả về serializer phù hợp tùy thuộc vào thao tác tạo mới hay xem danh sách."""
        if self.action in ["create", "register"]:
            return RegisterSerializer
        return NguoiDungSerializer

    def _is_manager(self, request):
        """Only the custom authenticated manager session may manage accounts."""
        return request.session.get("role") == "QuanLy" and request.session.get("user_id")

    def destroy(self, request, *args, **kwargs):
        """Deactivate a former employee while retaining audit/history references."""
        if not self._is_manager(request):
            return Response({"message": "Chỉ Quản lý được xóa tài khoản."}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()
        if user.ma_nguoi_dung == request.session.get("user_id"):
            return Response({"message": "Không thể xóa tài khoản đang đăng nhập."}, status=status.HTTP_400_BAD_REQUEST)
        if user.vai_tro and user.vai_tro.ten_vai_tro == "QuanLy":
            return Response({"message": "Không thể xóa tài khoản Quản lý từ màn hình này."}, status=status.HTTP_400_BAD_REQUEST)

        user.trang_thai = "Nghỉ việc"
        user.set_password(None)
        user.save(update_fields=["trang_thai", "mat_khau"])
        return Response({"message": f"Đã xóa tài khoản {user.ten_dang_nhap}."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        """Set a new password for an active employee account."""
        if not self._is_manager(request):
            return Response({"message": "Chỉ Quản lý được đặt lại mật khẩu."}, status=status.HTTP_403_FORBIDDEN)

        user = self.get_object()
        new_password = request.data.get("new_password", "")
        if len(new_password) < 6:
            return Response({"message": "Mật khẩu mới phải có ít nhất 6 ký tự."}, status=status.HTTP_400_BAD_REQUEST)
        if user.ma_nguoi_dung == request.session.get("user_id"):
            return Response({"message": "Hãy đổi mật khẩu Quản lý trong trang cài đặt."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["mat_khau"])
        return Response({"message": f"Đã đặt lại mật khẩu cho {user.ten_dang_nhap}."})


    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        """API hỗ trợ đăng ký tài khoản nhân viên mới."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Đăng ký tài khoản thành công!",
                    "user": NguoiDungSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
