"""Định tuyến các endpoint API thử nghiệm dành cho môi trường phát triển (development)."""

from django.http import JsonResponse
from django.urls import path


def seed(request):
    """Endpoint bảo vệ nhằm ngăn chặn nạp dữ liệu mẫu trái phép trong môi trường production."""
    if request.method != "POST":
        return JsonResponse({"code": "METHOD_NOT_ALLOWED", "message": "Phương thức không được hỗ trợ."}, status=405)
    return JsonResponse({"status": "seed-disabled", "message": "Seed chỉ được bật trong môi trường phát triển."}, status=403)


urlpatterns = [path("dev/seed", seed, name="seed")]

