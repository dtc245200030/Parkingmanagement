"""Định tuyến đường dẫn API báo cáo thống kê (/summary, /charts, /export/excel)."""

from django.urls import path
from apps.reports.views import charts_view, export_excel_view, summary_view

urlpatterns = [
    path("summary/", summary_view, name="reports-summary"),
    path("charts/", charts_view, name="reports-charts"),
    path("export/excel/", export_excel_view, name="reports-export-excel"),
]

