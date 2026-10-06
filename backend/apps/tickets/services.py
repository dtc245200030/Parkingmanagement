"""Các service nghiệp vụ xử lý tính tiền phí, định dạng thời gian, cho xe vào bãi (check-in) và cho xe ra bãi (check-out)."""

import math
from datetime import datetime
from decimal import Decimal
from django.utils import timezone

from apps.parking.models import BangGia, KhuVuc, ParkingSpot
from apps.tickets.models import LuotGuiXe, VeThang, VeXe
from apps.users.models import NguoiDung
from apps.vehicles.models import LoaiXe, PhuongTien


def calculate_fee(loai_xe, thoi_gian_vao, thoi_gian_ra=None, is_monthly=False):
    """Tính phí gửi xe dựa trên bảng giá thực tế trong CSDL (miễn phí nếu là vé tháng)."""
    if is_monthly:
        return Decimal("0.00")

    if thoi_gian_ra is None:
        thoi_gian_ra = timezone.now()

    # Default fallback pricing
    default_prices = {
        "MOTORBIKE": Decimal("5000"),
        "XeMay": Decimal("5000"),
        "CAR": Decimal("20000"),
        "Oto": Decimal("20000"),
        "Oto4Cho": Decimal("20000"),
        "Oto7Cho": Decimal("25000"),
        "BICYCLE": Decimal("2000"),
        "XeDap": Decimal("2000"),
        "XeTai": Decimal("30000"),
    }

    pricing = None
    if loai_xe:
        pricing = BangGia.objects.filter(loai_xe=loai_xe, loai_ap_dung="VeLuot").order_by("-ngay_ap_dung").first()

    base_price = pricing.gia_co_ban if pricing else default_prices.get(getattr(loai_xe, "ten_loai_xe", "XeMay"), Decimal("5000"))
    unit_minutes = pricing.don_vi_thoi_gian_phut if pricing else 60
    extra_price = pricing.gia_tang_them if pricing else Decimal("0.00")
    night_fee = pricing.gia_ban_dem if pricing else Decimal("0.00")

    duration_seconds = max(0, (thoi_gian_ra - thoi_gian_vao).total_seconds())
    duration_hours = max(1, math.ceil(duration_seconds / (unit_minutes * 60)))

    if extra_price > 0 and duration_hours > 1:
        total_fee = base_price + (Decimal(duration_hours - 1) * extra_price)
    else:
        total_fee = base_price * Decimal(duration_hours)

    if thoi_gian_ra.hour >= 22 or thoi_gian_ra.hour < 6:
        total_fee += night_fee

    return total_fee


def format_duration(thoi_gian_vao, thoi_gian_ra=None):
    """Tính toán và chuyển đổi khoảng thời gian gửi xe thành chuỗi văn bản dễ đọc."""
    if thoi_gian_ra is None:
        thoi_gian_ra = timezone.now()
    diff = thoi_gian_ra - thoi_gian_vao
    total_minutes = max(1, int(diff.total_seconds() // 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0:
        return f"{hours} giờ {minutes} phút" if minutes > 0 else f"{hours} giờ"
    return f"{minutes} phút"


def check_in_vehicle(plate_number, vehicle_type_name="XeMay", zone_name=None, staff_user=None, card_code=None):
    """Thực hiện quy trình ghi nhận xe vào bãi: kiểm tra trùng biển số, kiểm tra sức chứa khu vực và phát hành/kích hoạt thẻ giữ xe."""
    plate_number = plate_number.strip().upper()

    # Check if this plate is already active in lot
    existing_session = LuotGuiXe.objects.filter(
        bien_so_xe_kiem_tra=plate_number,
        trang_thai_luot="Đang gửi"
    ).first()
    if existing_session:
        zone_str = existing_session.khu_vuc.ten_khu_vuc if existing_session.khu_vuc else "N/A"
        raise ValueError(f"Xe mang biển số {plate_number} hiện ĐÃ CÓ lượt gửi trong bãi ({zone_str}). Vui lòng thanh toán lượt trước nếu xe đã ra.")

    # Determine or create LoaiXe
    loai_xe = None
    if vehicle_type_name:
        clean_vtype = vehicle_type_name.strip()
        loai_xe = LoaiXe.objects.filter(ten_loai_xe__iexact=clean_vtype).first()
        if not loai_xe:
            if clean_vtype.upper() in ["MOTORBIKE", "XE_MAY", "XEMAY", "XE MÁY", "XE MAY"]:
                loai_xe = LoaiXe.objects.filter(ten_loai_xe__in=["XeMay", "MOTORBIKE"]).first()
            elif clean_vtype.upper() in ["CAR", "OTO", "O_TO", "Ô TÔ", "O TO", "OTO4CHO", "OTO7CHO"]:
                loai_xe = LoaiXe.objects.filter(ten_loai_xe__in=["Oto", "CAR", "Oto4Cho"]).first()
            elif clean_vtype.upper() in ["BICYCLE", "XE_DAP", "XEDAP", "XE ĐẠP", "XE DAP", "BIKE"]:
                loai_xe = LoaiXe.objects.filter(ten_loai_xe__in=["XeDap", "BICYCLE"]).first()
            elif clean_vtype.upper() in ["TRUCK", "XE_TAI", "XETAI", "XE TẢI"]:
                loai_xe = LoaiXe.objects.filter(ten_loai_xe__in=["XeTai", "TRUCK"]).first()

    if not loai_xe:
        loai_xe = LoaiXe.objects.filter(ten_loai_xe="XeMay").first() or LoaiXe.objects.first()

    # Determine KhuVuc
    khu_vuc = None
    if zone_name:
        clean_zone = zone_name.strip()
        khu_vuc = KhuVuc.objects.filter(ten_khu_vuc__iexact=clean_zone).first()
        if not khu_vuc:
            last_char = clean_zone[-1].upper() if clean_zone else "A"
            khu_vuc = KhuVuc.objects.filter(ten_khu_vuc__icontains=last_char).first()

    if not khu_vuc:
        v_name = loai_xe.ten_loai_xe if loai_xe else "XeMay"
        if "XeMay" in v_name or "MOTORBIKE" in v_name:
            khu_vuc = KhuVuc.objects.filter(ten_khu_vuc="Khu A").first() or KhuVuc.objects.first()
        elif "Oto" in v_name or "CAR" in v_name:
            khu_vuc = KhuVuc.objects.filter(ten_khu_vuc="Khu C").first() or KhuVuc.objects.first()
        else:
            khu_vuc = KhuVuc.objects.filter(ten_khu_vuc="Khu B").first() or KhuVuc.objects.first()

    # Check zone capacity
    if khu_vuc:
        active_in_zone = LuotGuiXe.objects.filter(khu_vuc=khu_vuc, trang_thai_luot="Đang gửi").count()
        if active_in_zone >= khu_vuc.suc_chua_toi_da:
            raise ValueError(f"{khu_vuc.ten_khu_vuc} đã đạt sức chứa tối đa ({khu_vuc.suc_chua_toi_da} chỗ). Vui lòng chọn khu vực khác.")

    # Get or create PhuongTien
    phuong_tien, _ = PhuongTien.objects.get_or_create(
        bien_so_xe=plate_number,
        defaults={"loai_xe": loai_xe}
    )

    # Get or create card (VeXe)
    clean_plate_code = plate_number.replace("-", "").replace(".", "").replace(" ", "")
    if not card_code or not card_code.strip():
        card_code = f"CARD-{clean_plate_code}"

    ve_xe = VeXe.objects.filter(ma_dinh_danh_the=card_code).first()
    if not ve_xe:
        ve_xe = VeXe.objects.create(
            ma_dinh_danh_the=card_code,
            loai_the="Vé lượt",
            trang_thai_the="Đang gửi"
        )
    else:
        ve_xe.trang_thai_the = "Đang gửi"
        ve_xe.save()

    # Check if there is an active monthly ticket
    today = timezone.now().date()
    monthly_ticket = VeThang.objects.filter(
        phuong_tien=phuong_tien,
        trang_thai_ve="Còn hiệu lực",
        ngay_ket_thuc__gte=today
    ).first()

    if monthly_ticket:
        ve_xe.loai_the = "Vé tháng"
        ve_xe.save()

    # Determine staff user
    if not staff_user:
        staff_user = NguoiDung.objects.filter(trang_thai="Hoạt động").first()

    session = LuotGuiXe.objects.create(
        ve_xe=ve_xe,
        phuong_tien=phuong_tien,
        bien_so_xe_kiem_tra=plate_number,
        loai_xe=loai_xe,
        khu_vuc=khu_vuc,
        thoi_gian_vao=timezone.now(),
        nguoi_dung_vao=staff_user,
        trang_thai_luot="Đang gửi",
        tong_tien_phi=Decimal("0.00")
    )
    return session


def check_out_vehicle(session_id, staff_user=None):
    """Thực hiện quy trình cho xe ra bãi: tính tiền phí gửi xe, cập nhật thời gian ra và giải phóng trạng thái thẻ."""
    session = LuotGuiXe.objects.filter(pk=session_id).select_related("ve_xe", "loai_xe", "phuong_tien", "khu_vuc", "nguoi_dung_vao").first()
    if not session:
        raise ValueError("Không tìm thấy thông tin lượt gửi xe.")

    if session.trang_thai_luot == "Đã ra":
        raise ValueError("Lượt gửi này đã được hoàn tất trước đó.")

    now = timezone.now()
    session.thoi_gian_ra = now
    session.trang_thai_luot = "Đã ra"
    
    if staff_user:
        session.nguoi_dung_ra = staff_user
    elif not session.nguoi_dung_ra:
        session.nguoi_dung_ra = session.nguoi_dung_vao or NguoiDung.objects.first()

    # Check if monthly pass
    today = now.date()
    is_monthly = False
    if session.phuong_tien:
        is_monthly = VeThang.objects.filter(
            phuong_tien=session.phuong_tien,
            trang_thai_ve="Còn hiệu lực",
            ngay_ket_thuc__gte=today
        ).exists()

    session.tong_tien_phi = calculate_fee(session.loai_xe, session.thoi_gian_vao, now, is_monthly=is_monthly)
    session.save()

    # Free up card
    if session.ve_xe:
        session.ve_xe.trang_thai_the = "Sẵn sàng"
        session.ve_xe.save()

    return session

