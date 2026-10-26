"""Định tuyến các endpoint API thử nghiệm dành cho môi trường phát triển (development)."""

from django.http import JsonResponse
from django.urls import path

from . import views


def seed(request):
    """Endpoint bảo vệ nhằm ngăn chặn nạp dữ liệu mẫu trái phép trong môi trường production."""
    if request.method != "POST":
        return JsonResponse({"code": "METHOD_NOT_ALLOWED", "message": "Phương thức không được hỗ trợ."}, status=405)
    return JsonResponse({"status": "seed-disabled", "message": "Seed chỉ được bật trong môi trường phát triển."}, status=403)


urlpatterns = [
    path("dev/seed", seed, name="seed"),
    path("backups/", views.backups, name="backup-list"),
    path("backups/create/", views.create_database_backup, name="backup-create"),
    path("backups/restore/", views.restore_database_backup, name="backup-restore"),
    path("backups/<str:filename>/download/", views.download_database_backup, name="backup-download"),
]

