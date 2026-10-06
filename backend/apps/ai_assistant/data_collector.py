"""Thu thập dữ liệu thực 100% từ Django ORM (SQLite) để xây dựng context chuẩn xác cho AI."""

from datetime import timedelta
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from apps.parking.models import BangGia, KhuVuc
from apps.tickets.models import LuotGuiXe, VeThang
from apps.vehicles.models import LoaiXe


def collect_db_context() -> dict:
    """Tổng hợp toàn bộ dữ liệu thực tế từ Database."""
    now = timezone.now()

    # =========================================================
    # 1. TỔNG QUAN BÃI ĐỖ XE & KHU VỰC
    # =========================================================
    zones = list(KhuVuc.objects.all().order_by("ma_khu_vuc"))
    total_capacity = sum(z.suc_chua_toi_da for z in zones) or 300

    # Lượt xe đang gửi thực tế (dùng đúng chuỗi "Đang gửi" trong CSDL)
    active_sessions = LuotGuiXe.objects.filter(trang_thai_luot="Đang gửi").select_related("loai_xe", "khu_vuc")
    total_in_lot = active_sessions.count()
    total_available = max(0, total_capacity - total_in_lot)
    occupancy_rate = round((total_in_lot / total_capacity * 100), 1) if total_capacity > 0 else 0.0

    zone_details = []
    for z in zones:
        in_zone = active_sessions.filter(khu_vuc=z).count()
        available = max(0, z.suc_chua_toi_da - in_zone)
        rate = round((in_zone / z.suc_chua_toi_da * 100), 1) if z.suc_chua_toi_da > 0 else 0.0
        zone_details.append(
            f"  - {z.ten_khu_vuc}: {in_zone}/{z.suc_chua_toi_da} chỗ (còn trống: {available} chỗ, tỉ lệ lấp đầy: {rate}%)"
        )

    # =========================================================
    # 2. THỐNG KÊ LƯỢT XE ĐÃ HOÀN THÀNH & DOANH THU CSDL
    # =========================================================
    completed_sessions = LuotGuiXe.objects.filter(trang_thai_luot="Đã ra")
    completed_count = completed_sessions.count()
    total_all_sessions = LuotGuiXe.objects.count()

    total_revenue_agg = completed_sessions.aggregate(s=Sum("tong_tien_phi"))
    total_revenue = float(total_revenue_agg["s"] or 0)

    # Thống kê theo ngày mới nhất trong DB
    latest_session = LuotGuiXe.objects.order_by("-thoi_gian_vao").first()
    latest_date_str = latest_session.thoi_gian_vao.strftime("%d/%m/%Y") if latest_session else "N/A"

    # =========================================================
    # 3. THỐNG KÊ THEO LOẠI XE (ĐANG GỬI)
    # =========================================================
    vehicle_type_stats = []
    for lx in LoaiXe.objects.all():
        cnt = active_sessions.filter(loai_xe=lx).count()
        total_cnt = LuotGuiXe.objects.filter(loai_xe=lx).count()
        vehicle_type_stats.append(f"  - {lx.ten_loai_xe}: {cnt} xe đang gửi (tổng {total_cnt} lượt gửi trong CSDL)")

    # =========================================================
    # 4. VÉ THÁNG (dùng đúng chuỗi "Còn hiệu lực" trong CSDL)
    # =========================================================
    today_date = now.date()
    monthly_active = VeThang.objects.filter(trang_thai_ve="Còn hiệu lực").count()
    monthly_expired = VeThang.objects.filter(trang_thai_ve="Đã hết hạn").count()
    monthly_total = VeThang.objects.count()

    monthly_details = []
    for vt in VeThang.objects.all().select_related("phuong_tien", "phuong_tien__loai_xe"):
        bs = vt.phuong_tien.bien_so_xe if vt.phuong_tien else "N/A"
        monthly_details.append(
            f"  - {vt.ho_ten_khach_hang} | BSK: {bs} | SĐT: {vt.so_dien_thoai or 'N/A'} | Hạn: {vt.ngay_ket_thuc.strftime('%d/%m/%Y')} | Trạng thái: {vt.trang_thai_ve}"
        )

    # =========================================================
    # 5. BẢNG GIÁ
    # =========================================================
    pricing_info = []
    for bg in BangGia.objects.all().select_related("loai_xe"):
        pricing_info.append(
            f"  - {bg.loai_xe.ten_loai_xe} ({bg.get_loai_ap_dung_display()}): "
            f"Giá cơ bản {bg.gia_co_ban:,.0f} VNĐ/{bg.don_vi_thoi_gian_phut} phút"
            + (f", tăng thêm {bg.gia_tang_them:,.0f} VNĐ/chu kỳ" if float(bg.gia_tang_them) > 0 else "")
            + (f", phụ phí đêm {bg.gia_ban_dem:,.0f} VNĐ" if float(bg.gia_ban_dem) > 0 else "")
        )

    # =========================================================
    # 6. PHÂN BỐ GIỜ CAO ĐIỂM (Tất cả lượt xe)
    # =========================================================
    hourly_counts = {}
    for session in LuotGuiXe.objects.all():
        h = session.thoi_gian_vao.hour
        hourly_counts[h] = hourly_counts.get(h, 0) + 1

    peak_hour = max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else (8, 0)
    hourly_summary = [f"  {h:02d}h-{h+1:02d}h: {cnt} lượt" for h, cnt in sorted(hourly_counts.items())]

    # =========================================================
    # COMPILE CONTEXT TEXT
    # =========================================================
    context = f"""
=== DỮ LIỆU THỰC TẾ TRONG CƠ SỞ DỮ LIỆU BÃI XE (Cập nhật lúc {now.strftime('%H:%M %d/%m/%Y')}) ===

[1. TRẠNG THÁI BÃI ĐỖ XE HIỆN TẠI]
- Sức chứa tối đa toàn bãi: {total_capacity} chỗ
- Số xe ĐANG GỬI thực tế trong bãi: {total_in_lot} xe
- Số chỗ còn trống: {total_available} chỗ
- Tỉ lệ lấp đầy hiện tại: {occupancy_rate}%
- Chi tiết theo từng khu vực:
{chr(10).join(zone_details) if zone_details else '  (Chưa có dữ liệu)'}

[2. TỔNG HỢP LƯỢT XE & DOANH THU TOÀN BÃI]
- Tổng số lượt gửi xe trong CSDL: {total_all_sessions} lượt
- Số lượt xe đã ra (hoàn thành): {completed_count} lượt
- Số xe đang đỗ (chưa ra): {total_in_lot} lượt
- TỔNG DOANH THU TÍCH LŨY TRONG CSDL: {total_revenue:,.0f} VNĐ
- Ngày ghi nhận dữ liệu lượt xe gần nhất: {latest_date_str}

[3. PHÂN BỐ XE ĐANG GỬI THEO LOẠI XE]
{chr(10).join(vehicle_type_stats) if vehicle_type_stats else '  (Chưa có dữ liệu)'}

[4. KHUNG GIỜ CAO ĐIỂM (TỔNG HỢP TOÀN BỘ LƯỢT XE)]
- Khung giờ đông xe nhất: {peak_hour[0]:02d}h-{peak_hour[0]+1:02d}h với {peak_hour[1]} lượt xe vào.
- Phân bố chi tiết theo giờ:
{chr(10).join(hourly_summary) if hourly_summary else '  (Chưa có dữ liệu)'}

[5. QUẢN LÝ VÉ THÁNG]
- Tổng số khách hàng vé tháng: {monthly_total} vé
- Vé tháng còn hiệu lực: {monthly_active} vé
- Vé tháng đã hết hạn: {monthly_expired} vé
- Danh sách chi tiết vé tháng:
{chr(10).join(monthly_details) if monthly_details else '  (Chưa có vé tháng)'}

[6. BẢNG GIÁ ÁP DỤNG]
{chr(10).join(pricing_info) if pricing_info else '  (Chưa có bảng giá)'}
"""
    return {
        "context_text": context,
        "summary": {
            "total_capacity": total_capacity,
            "total_in_lot": total_in_lot,
            "total_available": total_available,
            "occupancy_rate": occupancy_rate,
            "total_revenue": total_revenue,
            "total_all_sessions": total_all_sessions,
            "peak_hour": peak_hour[0],
            "peak_hour_count": peak_hour[1],
            "monthly_active": monthly_active,
        },
    }
