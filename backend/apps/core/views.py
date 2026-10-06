"""Views kiểm tra trạng thái hoạt động (health check) của ứng dụng."""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Kiểm tra sức khỏe hệ thống (Health check status)."""
    return JsonResponse({"status": "ok", "app": "ParkAI Manager", "version": "2.0.0"})

