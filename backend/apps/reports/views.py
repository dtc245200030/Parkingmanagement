"""API views phục vụ xuất báo cáo dữ liệu, biểu đồ phân tích và file Excel download."""

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.reports.services import generate_excel_report, get_chart_data, get_realtime_summary


@api_view(["GET"])
@permission_classes([AllowAny])
def summary_view(request):
    """API trả về các chỉ số thống kê tổng quan thời gian thực."""
    data = get_realtime_summary()
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def charts_view(request):
    """API trả về dữ liệu biểu đồ phân tích theo giờ, ngày và tỷ lệ khu vực."""
    data = get_chart_data()
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def export_excel_view(request):
    """API xuất file Excel báo cáo định dạng .xlsx cho lượt xe hoặc vé tháng."""
    report_type = request.query_params.get("type", "history")
    excel_stream = generate_excel_report(report_type=report_type)

    filename = f"ParkAI_BaoCao_{report_type}.xlsx"
    response = HttpResponse(
        excel_stream.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

