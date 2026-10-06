"""Serializers cho Vé xe, Lượt gửi xe và Vé tháng."""

from rest_framework import serializers
from apps.parking.serializers import KhuVucSerializer
from apps.tickets.models import LuotGuiXe, VeThang, VeXe
from apps.tickets.services import calculate_fee, format_duration
from apps.vehicles.serializers import LoaiXeSerializer, PhuongTienSerializer


class VeXeSerializer(serializers.ModelSerializer):
    """Serializer cho mô hình Vé/Thẻ xe."""

    class Meta:
        model = VeXe
        fields = ["ma_ve", "ma_dinh_danh_the", "loai_the", "trang_thai_the"]


class LuotGuiXeSerializer(serializers.ModelSerializer):
    """Serializer dữ liệu Lượt gửi xe chi tiết phục vụ hiển thị lịch sử và xe đang gửi."""

    ve_xe_detail = VeXeSerializer(source="ve_xe", read_only=True)
    loai_xe_detail = LoaiXeSerializer(source="loai_xe", read_only=True)
    khu_vuc_detail = KhuVucSerializer(source="khu_vuc", read_only=True)
    ten_khu_vuc = serializers.CharField(source="khu_vuc.ten_khu_vuc", read_only=True)
    ten_loai_xe = serializers.CharField(source="loai_xe.ten_loai_xe", read_only=True)
    ma_the_rfid = serializers.CharField(source="ve_xe.ma_dinh_danh_the", read_only=True)
    loai_the = serializers.CharField(source="ve_xe.loai_the", read_only=True)
    thoi_gian_gui_text = serializers.SerializerMethodField()
    tien_phi_du_tinh = serializers.SerializerMethodField()
    ten_khach_hang = serializers.SerializerMethodField()
    ten_nhan_vien_vao = serializers.SerializerMethodField()
    ten_nhan_vien_ra = serializers.SerializerMethodField()

    class Meta:
        model = LuotGuiXe
        fields = [
            "ma_luot_gui",
            "ve_xe",
            "ve_xe_detail",
            "ma_the_rfid",
            "loai_the",
            "phuong_tien",
            "bien_so_xe_kiem_tra",
            "loai_xe",
            "loai_xe_detail",
            "ten_loai_xe",
            "khu_vuc",
            "khu_vuc_detail",
            "ten_khu_vuc",
            "vi_tri",
            "thoi_gian_vao",
            "thoi_gian_ra",
            "thoi_gian_gui_text",
            "tien_phi_du_tinh",
            "nguoi_dung_vao",
            "nguoi_dung_ra",
            "ten_nhan_vien_vao",
            "ten_nhan_vien_ra",
            "tong_tien_phi",
            "trang_thai_luot",
            "ten_khach_hang",
        ]

    def get_thoi_gian_gui_text(self, obj):
        """Định dạng thời gian gửi xe thành dạng text thân thiện (ví dụ: '2 giờ 15 phút')."""
        return format_duration(obj.thoi_gian_vao, obj.thoi_gian_ra)

    def get_tien_phi_du_tinh(self, obj):
        """Tính số tiền phí tạm tính hiện tại dựa trên bảng giá và thời gian gửi."""
        if obj.trang_thai_luot == "Đã ra":
            return float(obj.tong_tien_phi)
        return float(calculate_fee(obj.loai_xe, obj.thoi_gian_vao))

    def get_ten_khach_hang(self, obj):
        """Lấy tên khách hàng nếu sở hữu vé tháng hoặc trả về 'Khách vãng lai'."""
        if obj.phuong_tien:
            vt = VeThang.objects.filter(phuong_tien=obj.phuong_tien).first()
            if vt:
                return vt.ho_ten_khach_hang
        return "Khách vãng lai"

    def get_ten_nhan_vien_vao(self, obj):
        """Lấy họ tên nhân viên ghi nhận lượt vào."""
        if obj.nguoi_dung_vao:
            return obj.nguoi_dung_vao.ho_ten
        return "Trần Thị Mai (Trực ca)"

    def get_ten_nhan_vien_ra(self, obj):
        """Lấy họ tên nhân viên ghi nhận lượt ra."""
        if obj.nguoi_dung_ra:
            return obj.nguoi_dung_ra.ho_ten
        if obj.trang_thai_luot == "Đã ra":
            return obj.nguoi_dung_vao.ho_ten if obj.nguoi_dung_vao else "Lê Văn Hùng"
        return "Chưa ghi nhận (Xe đang gửi)"



class VeThangSerializer(serializers.ModelSerializer):
    """Serializer quản lý thông tin đăng ký và gia hạn vé tháng."""

    the_xe_detail = VeXeSerializer(source="the_xe", read_only=True)
    phuong_tien_detail = PhuongTienSerializer(source="phuong_tien", read_only=True)
    bien_so_xe = serializers.CharField(source="phuong_tien.bien_so_xe", read_only=True)
    ten_loai_xe = serializers.CharField(source="phuong_tien.loai_xe.ten_loai_xe", read_only=True)
    ma_the_rfid = serializers.CharField(source="the_xe.ma_dinh_danh_the", read_only=True)

    class Meta:
        model = VeThang
        fields = [
            "ma_ve_thang",
            "the_xe",
            "the_xe_detail",
            "ma_the_rfid",
            "phuong_tien",
            "phuong_tien_detail",
            "bien_so_xe",
            "ten_loai_xe",
            "ho_ten_khach_hang",
            "so_dien_thoai",
            "ngay_bat_dau",
            "ngay_ket_thuc",
            "moi_gia_han",
            "trang_thai_ve",
        ]


class CheckInRequestSerializer(serializers.Serializer):
    plate_number = serializers.CharField(required=True)
    vehicle_type = serializers.CharField(required=False, default="XeMay")
    zone = serializers.CharField(required=False, default="Khu A")
    card_code = serializers.CharField(required=False, allow_blank=True, default="")
    staff_id = serializers.IntegerField(required=False, allow_null=True)
    staff_username = serializers.CharField(required=False, allow_blank=True, default="")


class CheckOutRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=False)
    plate_number = serializers.CharField(required=False, allow_blank=True)
    staff_id = serializers.IntegerField(required=False, allow_null=True)
    staff_username = serializers.CharField(required=False, allow_blank=True, default="")
