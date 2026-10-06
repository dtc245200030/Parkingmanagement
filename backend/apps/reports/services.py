"""Các hàm dịch vụ tổng hợp số liệu báo cáo thời gian thực, dữ liệu biểu đồ và xuất báo cáo Excel (.xlsx)."""

import io
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Count, Sum
from django.utils import timezone
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from apps.parking.models import KhuVuc
from apps.tickets.models import LuotGuiXe, VeThang, VeXe
from apps.users.models import NguoiDung


def get_realtime_summary():
    """Tổng hợp toàn bộ chỉ số thực tế 100% từ Database (sức chứa, lượt xe, doanh thu, vé tháng)."""

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)

    # 1. Total capacity & Zones
    zones = list(KhuVuc.objects.all().order_by("ma_khu_vuc"))
    total_capacity = sum(z.suc_chua_toi_da for z in zones) or 300

    # 2. In lot active vehicles
    active_sessions = list(LuotGuiXe.objects.filter(trang_thai_luot="Đang gửi").select_related("loai_xe", "khu_vuc", "phuong_tien"))
    total_in_lot = len(active_sessions)
    total_available = max(0, total_capacity - total_in_lot)
    occupancy_rate = round((total_in_lot / total_capacity * 100), 1) if total_capacity > 0 else 0.0

    # Zone stats
    zone_stats = []
    for z in zones:
        in_zone = sum(1 for s in active_sessions if s.khu_vuc_id == z.ma_khu_vuc)
        available = max(0, z.suc_chua_toi_da - in_zone)
        rate = round((in_zone / z.suc_chua_toi_da * 100), 1) if z.suc_chua_toi_da > 0 else 0.0
        zone_stats.append({
            "code": z.ten_khu_vuc.replace("Khu ", "").strip(),
            "name": z.ten_khu_vuc,
            "desc": z.mo_ta or "",
            "capacity": z.suc_chua_toi_da,
            "in_lot": in_zone,
            "available": available,
            "rate": rate,
        })

    # 3. Today stats
    today_in_count = LuotGuiXe.objects.filter(thoi_gian_vao__gte=today_start).count()
    today_out_count = LuotGuiXe.objects.filter(thoi_gian_ra__gte=today_start, trang_thai_luot="Đã ra").count()
    today_revenue_agg = LuotGuiXe.objects.filter(thoi_gian_ra__gte=today_start, trang_thai_luot="Đã ra").aggregate(total=Sum("tong_tien_phi"))
    today_revenue = float(today_revenue_agg["total"] or 0)

    # 4. Weekly stats
    week_entries = LuotGuiXe.objects.filter(thoi_gian_vao__gte=week_start).count()
    week_revenue_agg = LuotGuiXe.objects.filter(thoi_gian_ra__gte=week_start, trang_thai_luot="Đã ra").aggregate(total=Sum("tong_tien_phi"))
    week_revenue = float(week_revenue_agg["total"] or 0)
    avg_daily_entries = round(week_entries / 7, 0) if week_entries > 0 else 0

    # 5. Monthly tickets count
    today_date = now.date()
    monthly_active = VeThang.objects.filter(trang_thai_ve="Còn hiệu lực", ngay_ket_thuc__gte=today_date).count()
    monthly_expired = VeThang.objects.filter(ngay_ket_thuc__lt=today_date).count()
    monthly_total = VeThang.objects.count()

    return {
        "total_capacity": total_capacity,
        "total_in_lot": total_in_lot,
        "total_available": total_available,
        "occupancy_rate": occupancy_rate,
        "today_in_count": today_in_count,
        "today_out_count": today_out_count,
        "today_revenue": today_revenue,
        "week_entries": week_entries,
        "week_revenue": week_revenue,
        "avg_daily_entries": avg_daily_entries,
        "monthly_active": monthly_active,
        "monthly_expired": monthly_expired,
        "monthly_total": monthly_total,
        "zone_stats": zone_stats,
    }


def get_chart_data():
    """Lấy số liệu thực tế theo ngày và theo giờ cho biểu đồ Chart.js"""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Hourly distribution today (6h to 21h)
    hours = list(range(6, 22))
    hourly_labels = [f"{h}h" for h in hours]
    hourly_entries = []
    for h in hours:
        h_start = today_start.replace(hour=h)
        h_end = h_start + timedelta(hours=1)
        cnt = LuotGuiXe.objects.filter(thoi_gian_vao__gte=h_start, thoi_gian_vao__lt=h_end).count()
        hourly_entries.append(cnt)

    # 2. 7-Day daily traffic and revenue
    daily_labels = []
    daily_traffic = []
    daily_revenue = []
    weekday_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

    for i in range(6, -1, -1):
        day_date = today_start - timedelta(days=i)
        day_end = day_date + timedelta(days=1)
        w_idx = day_date.weekday()
        daily_labels.append(weekday_vn[w_idx])

        cnt = LuotGuiXe.objects.filter(thoi_gian_vao__gte=day_date, thoi_gian_vao__lt=day_end).count()
        rev_agg = LuotGuiXe.objects.filter(thoi_gian_ra__gte=day_date, thoi_gian_ra__lt=day_end).aggregate(s=Sum("tong_tien_phi"))
        rev_mil = round(float(rev_agg["s"] or 0) / 1_000_000, 2)

        daily_traffic.append(cnt)
        daily_revenue.append(rev_mil)

    # 3. Zone share percentage
    zones = KhuVuc.objects.all().order_by("ma_khu_vuc")
    zone_labels = [z.ten_khu_vuc for z in zones]
    zone_counts = []
    total_zone_sessions = LuotGuiXe.objects.count() or 1
    for z in zones:
        cnt = LuotGuiXe.objects.filter(khu_vuc=z).count()
        zone_counts.append(round((cnt / total_zone_sessions) * 100, 1))

    return {
        "hourly": {"labels": hourly_labels, "data": hourly_entries},
        "daily": {"labels": daily_labels, "traffic": daily_traffic, "revenue": daily_revenue},
        "zone_distribution": {"labels": zone_labels, "data": zone_counts},
    }


def generate_excel_report(report_type="history"):
    """Tạo file Excel (.xlsx) báo cáo chuyên nghiệp bằng openpyxl"""
    wb = openpyxl.Workbook()
    ws = wb.active

    # Styles
    title_font = Font(name="Arial", size=16, bold=True, color="002060")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Arial", size=10)
    bold_font = Font(name="Arial", size=10, bold=True)
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    subtotal_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    now_str = timezone.now().strftime("%d/%m/%Y %H:%M:%S")

    if report_type == "monthly":
        ws.title = "Báo Cáo Vé Tháng"
        ws.merge_cells("A1:G1")
        ws["A1"] = "DANH SÁCH KHÁCH HÀNG VÉ THÁNG - PARKAI MANAGER"
        ws["A1"].font = title_font
        ws["A1"].alignment = center_align

        ws["A2"] = f"Thời điểm xuất báo cáo: {now_str}"
        ws["A2"].font = Font(name="Arial", size=9, italic=True)

        headers = ["STT", "Họ tên khách hàng", "Số điện thoại", "Biển số xe", "Loại xe", "Hạn hiệu lực", "Trạng thái"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = thin_border

        tickets = VeThang.objects.all().select_related("phuong_tien", "phuong_tien__loai_xe").order_by("-ma_ve_thang")
        row_idx = 5
        for idx, vt in enumerate(tickets, 1):
            v_type = vt.phuong_tien.loai_xe.ten_loai_xe if vt.phuong_tien and vt.phuong_tien.loai_xe else "N/A"
            ws.cell(row=row_idx, column=1, value=idx).alignment = center_align
            ws.cell(row=row_idx, column=2, value=vt.ho_ten_khach_hang).alignment = left_align
            ws.cell(row=row_idx, column=3, value=vt.so_dien_thoai or "N/A").alignment = center_align
            ws.cell(row=row_idx, column=4, value=vt.phuong_tien.bien_so_xe if vt.phuong_tien else "N/A").alignment = center_align
            ws.cell(row=row_idx, column=5, value=v_type).alignment = center_align
            ws.cell(row=row_idx, column=6, value=vt.ngay_ket_thuc.strftime("%d/%m/%Y")).alignment = center_align
            ws.cell(row=row_idx, column=7, value=vt.trang_thai_ve).alignment = center_align

            for c in range(1, 8):
                ws.cell(row=row_idx, column=c).border = thin_border
                ws.cell(row=row_idx, column=c).font = data_font
            row_idx += 1

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    else:
        # Default: History / General Transaction Report
        ws.title = "Báo Cáo Lượt Xe"
        ws.merge_cells("A1:H1")
        ws["A1"] = "BÁO CÁO CHI TIẾT LƯỢT XE VÀO / RA - PARKAI"
        ws["A1"].font = title_font
        ws["A1"].alignment = center_align

        ws["A2"] = f"Thời điểm xuất file: {now_str}"
        ws["A2"].font = Font(name="Arial", size=9, italic=True)

        headers = ["STT", "Biển số xe", "Loại xe", "Khu vực", "Thời gian vào", "Thời gian ra", "Tiền phí (VNĐ)", "Trạng thái"]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = thin_border

        sessions = LuotGuiXe.objects.all().select_related("loai_xe", "khu_vuc").order_by("-thoi_gian_vao")
        row_idx = 5
        total_revenue = Decimal("0.00")

        for idx, s in enumerate(sessions, 1):
            v_type = s.loai_xe.ten_loai_xe if s.loai_xe else "N/A"
            zone = s.khu_vuc.ten_khu_vuc if s.khu_vuc else "N/A"
            in_str = s.thoi_gian_vao.strftime("%d/%m/%Y %H:%M")
            out_str = s.thoi_gian_ra.strftime("%d/%m/%Y %H:%M") if s.thoi_gian_ra else "--"
            fee = float(s.tong_tien_phi)
            total_revenue += Decimal(str(fee))

            ws.cell(row=row_idx, column=1, value=idx).alignment = center_align
            ws.cell(row=row_idx, column=2, value=s.bien_so_xe_kiem_tra).alignment = center_align
            ws.cell(row=row_idx, column=3, value=v_type).alignment = center_align
            ws.cell(row=row_idx, column=4, value=zone).alignment = center_align
            ws.cell(row=row_idx, column=5, value=in_str).alignment = center_align
            ws.cell(row=row_idx, column=6, value=out_str).alignment = center_align
            
            fee_cell = ws.cell(row=row_idx, column=7, value=fee)
            fee_cell.alignment = right_align
            fee_cell.number_format = "#,##0"

            ws.cell(row=row_idx, column=8, value=s.trang_thai_luot).alignment = center_align

            for c in range(1, 9):
                ws.cell(row=row_idx, column=c).border = thin_border
                ws.cell(row=row_idx, column=c).font = data_font
            row_idx += 1

        # Summary row
        ws.cell(row=row_idx, column=1, value="TỔNG CỘNG").font = bold_font
        ws.cell(row=row_idx, column=1).alignment = center_align
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
        
        tot_cell = ws.cell(row=row_idx, column=7, value=float(total_revenue))
        tot_cell.font = bold_font
        tot_cell.alignment = right_align
        tot_cell.number_format = "#,##0"

        ws.cell(row=row_idx, column=8, value=f"{len(sessions)} lượt").font = bold_font
        ws.cell(row=row_idx, column=8).alignment = center_align

        for c in range(1, 9):
            ws.cell(row=row_idx, column=c).fill = subtotal_fill
            ws.cell(row=row_idx, column=c).border = thin_border

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
