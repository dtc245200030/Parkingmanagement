"""API Views và ViewSets quản lý vé xe, lượt gửi xe (check-in/check-out) và đăng ký/gia hạn vé tháng."""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.parking.models import KhuVuc
from apps.tickets.models import LuotGuiXe, VeThang
from apps.tickets.serializers import (
    CheckInRequestSerializer,
    CheckOutRequestSerializer,
    LuotGuiXeSerializer,
    VeThangSerializer,
)
from apps.tickets.services import check_in_vehicle, check_out_vehicle
from apps.users.models import NguoiDung
from apps.vehicles.models import LoaiXe, PhuongTien


@api_view(["POST"])
@permission_classes([AllowAny])
def check_in_api(request):
    """API endpoint xử lý ghi nhận xe vào bãi đỗ."""
    serializer = CheckInRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"status": "error", "errors": serializer.errors, "message": "Dữ liệu gửi xe không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

    plate = serializer.validated_data["plate_number"]
    v_type = serializer.validated_data.get("vehicle_type", "XeMay")
    zone = serializer.validated_data.get("zone", "Khu A")

    # Determine staff user
    staff_id = serializer.validated_data.get("staff_id") or request.session.get("user_id")
    staff_username = serializer.validated_data.get("staff_username") or request.session.get("username")

    staff = None
    if staff_id:
        staff = NguoiDung.objects.filter(pk=staff_id).first()
    if not staff and staff_username:
        staff = NguoiDung.objects.filter(ten_dang_nhap__iexact=staff_username).first()
    if not staff:
        staff = NguoiDung.objects.filter(vai_tro__ten_vai_tro__in=["NhanVien", "QuanLy"]).first() or NguoiDung.objects.first()

    try:
        session = check_in_vehicle(
            plate_number=plate,
            vehicle_type_name=v_type,
            zone_name=zone,
            staff_user=staff,
        )
        return Response(
            {
                "status": "success",
                "message": f"Ghi nhận xe {session.bien_so_xe_kiem_tra} vào {session.khu_vuc.ten_khu_vuc if session.khu_vuc else 'bãi'} thành công!",
                "session": LuotGuiXeSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )
    except ValueError as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"status": "error", "message": f"Lỗi xử lý: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def check_out_api(request):
    """API endpoint xử lý ghi nhận xe ra bãi và tính phí gửi xe."""
    serializer = CheckOutRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"status": "error", "errors": serializer.errors, "message": "Dữ liệu xe ra không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data.get("session_id")
    plate = serializer.validated_data.get("plate_number")

    if not session_id and plate:
        sess = LuotGuiXe.objects.filter(
            bien_so_xe_kiem_tra__iexact=plate.strip().upper(),
            trang_thai_luot="Đang gửi",
        ).first()
        if sess:
            session_id = sess.ma_luot_gui

    if not session_id:
        return Response({"status": "error", "message": "Vui lòng chọn lượt xe cần thanh toán / ra bãi."}, status=status.HTTP_400_BAD_REQUEST)

    staff_id = serializer.validated_data.get("staff_id") or request.session.get("user_id")
    staff_username = serializer.validated_data.get("staff_username") or request.session.get("username")

    staff = None
    if staff_id:
        staff = NguoiDung.objects.filter(pk=staff_id).first()
    if not staff and staff_username:
        staff = NguoiDung.objects.filter(ten_dang_nhap__iexact=staff_username).first()
    if not staff:
        staff = NguoiDung.objects.filter(vai_tro__ten_vai_tro__in=["NhanVien", "QuanLy"]).first() or NguoiDung.objects.first()

    try:
        session = check_out_vehicle(session_id=session_id, staff_user=staff)
        return Response(
            {
                "status": "success",
                "message": f"Xe {session.bien_so_xe_kiem_tra} đã ra bãi. Phí thu: {session.tong_tien_phi:,.0f} đ",
                "session": LuotGuiXeSerializer(session).data,
            },
            status=status.HTTP_200_OK,
        )
    except ValueError as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"status": "error", "message": f"Lỗi xử lý: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LuotGuiXeViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý tìm kiếm, lọc và xem chi tiết danh sách lượt gửi xe."""

    queryset = LuotGuiXe.objects.all().select_related("loai_xe", "khu_vuc", "phuong_tien", "nguoi_dung_vao", "nguoi_dung_ra").order_by("-thoi_gian_vao")
    serializer_class = LuotGuiXeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Lọc danh sách lượt gửi xe theo trạng thái, khu vực và từ khóa tìm kiếm."""
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        zone_filter = self.request.query_params.get("zone")
        search_query = self.request.query_params.get("q")

        if status_filter:
            if status_filter == "inlot":
                qs = qs.filter(trang_thai_luot="Đang gửi")
            elif status_filter == "completed":
                qs = qs.filter(trang_thai_luot="Đã ra")
            else:
                qs = qs.filter(trang_thai_luot=status_filter)

        if zone_filter:
            qs = qs.filter(khu_vuc__ten_khu_vuc__icontains=zone_filter)

        if search_query:
            clean_q = search_query.strip().upper()
            qs = qs.filter(
                Q(bien_so_xe_kiem_tra__icontains=clean_q)
                | Q(phuong_tien__bien_so_xe__icontains=clean_q)
                | Q(nguoi_dung_vao__ho_ten__icontains=search_query)
            )

        return qs

    @action(detail=False, methods=["get"])
    def in_lot(self, request):
        """API trả về danh sách các phương tiện hiện đang ở trong bãi đỗ."""
        qs = self.get_queryset().filter(trang_thai_luot="Đang gửi")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Xóa thông tin lượt gửi xe khỏi hệ thống."""
        instance = self.get_object()
        plate = instance.bien_so_xe_kiem_tra
        self.perform_destroy(instance)
        return Response(
            {
                "status": "success",
                "message": f"Đã xóa lượt gửi xe {plate} khỏi hệ thống thành công!",
            },
            status=status.HTTP_200_OK,
        )


class VeThangViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý CRUD vé tháng và gia hạn thời gian sử dụng."""

    queryset = VeThang.objects.all().select_related("phuong_tien", "phuong_tien__loai_xe").order_by("-ma_ve_thang")
    serializer_class = VeThangSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Đăng ký vé tháng mới cho khách hàng."""
        data = request.data
        name = data.get("name") or data.get("ho_ten_khach_hang")
        phone = data.get("phone") or data.get("so_dien_thoai", "")
        plate = (data.get("plate") or data.get("bien_so_xe", "")).strip().upper()
        v_type_str = data.get("type") or data.get("ten_loai_xe", "XeMay")
        expiry = data.get("expiry") or data.get("ngay_ket_thuc")
        start = data.get("start_date") or data.get("ngay_bat_dau")

        from django.utils import timezone
        if not start:
            start = timezone.now().date()

        if not name or not plate:
            return Response({"message": "Vui lòng cung cấp họ tên và biển số xe."}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create LoaiXe
        loai_xe = LoaiXe.objects.filter(ten_loai_xe__iexact=v_type_str).first()
        if not loai_xe:
            loai_xe = LoaiXe.objects.filter(ten_loai_xe="XeMay").first() or LoaiXe.objects.first()

        # Get or create PhuongTien
        phuong_tien, _ = PhuongTien.objects.get_or_create(
            bien_so_xe=plate,
            defaults={"loai_xe": loai_xe}
        )

        ve_thang = VeThang.objects.create(
            phuong_tien=phuong_tien,
            ho_ten_khach_hang=name,
            so_dien_thoai=phone,
            ngay_bat_dau=start,
            ngay_ket_thuc=expiry,
            trang_thai_ve="Còn hiệu lực",
        )
        return Response(
            {
                "status": "success",
                "message": f"Đăng ký vé tháng thành công cho khách hàng {name}!",
                "data": VeThangSerializer(ve_thang).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        """Hủy vé tháng của phương tiện."""
        instance = self.get_object()
        cust_name = instance.ho_ten_khach_hang
        plate = instance.phuong_tien.bien_so_xe if instance.phuong_tien else ""
        self.perform_destroy(instance)

        return Response(
            {
                "status": "success",
                "message": f"Đã xóa vé tháng của khách hàng {cust_name} (Biển số: {plate}) thành công!",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        """Gia hạn vé tháng - kéo dài thời hạn sử dụng."""
        instance = self.get_object()
        data = request.data

        from django.utils import timezone as tz
        from datetime import timedelta

        # Number of months to renew (default 1)
        months = int(data.get("months", 1))
        new_end_date_str = data.get("new_end_date")

        today = tz.now().date()

        if new_end_date_str:
            from datetime import datetime
            try:
                new_end = datetime.strptime(new_end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"status": "error", "message": "Ngày gia hạn không hợp lệ (YYYY-MM-DD)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            base_date = max(instance.ngay_ket_thuc, today)
            # Add approx 30 days per month
            new_end = base_date + timedelta(days=30 * months)

        if new_end <= today:
            return Response(
                {"status": "error", "message": "Ngày gia hạn phải sau ngày hôm nay."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.ngay_ket_thuc = new_end
        instance.trang_thai_ve = "Còn hiệu lực"
        instance.moi_gia_han = True
        instance.save()

        return Response(
            {
                "status": "success",
                "message": f"Đã gia hạn vé tháng cho {instance.ho_ten_khach_hang} đến ngày {new_end.strftime('%d/%m/%Y')}!",
                "data": VeThangSerializer(instance).data,
            },
            status=status.HTTP_200_OK,
        )
