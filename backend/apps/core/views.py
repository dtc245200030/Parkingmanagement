"""Core views: health check and manager database maintenance."""

import json

from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.users.models import NguoiDung
from .backup_service import BackupError, create_backup, list_backups, resolve_backup, restore_database, save_uploaded_backup


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return JsonResponse({"status": "ok", "app": "ParkAI Manager", "version": "2.0.0"})


def _manager_or_error(request):
    user_id = request.session.get("user_id")
    if request.session.get("role") != "QuanLy" or not user_id:
        return JsonResponse({"code": "FORBIDDEN", "message": "Chỉ Quản lý bãi mới được sao lưu và khôi phục."}, status=403)
    if not NguoiDung.objects.filter(ma_nguoi_dung=user_id, vai_tro__ten_vai_tro="QuanLy").exists():
        return JsonResponse({"code": "FORBIDDEN", "message": "Phiên đăng nhập không còn quyền Quản lý."}, status=403)
    return None


@require_http_methods(["GET"])
def backups(request):
    denied = _manager_or_error(request)
    return denied or JsonResponse({"backups": list_backups()})


@csrf_protect
@require_http_methods(["POST"])
def create_database_backup(request):
    denied = _manager_or_error(request)
    if denied:
        return denied
    try:
        path = create_backup()
        return JsonResponse({"status": "success", "message": "Đã tạo bản sao lưu an toàn.", "filename": path.name}, status=201)
    except BackupError as exc:
        return JsonResponse({"code": "BACKUP_FAILED", "message": str(exc)}, status=400)


@require_http_methods(["GET"])
def download_database_backup(request, filename):
    denied = _manager_or_error(request)
    if denied:
        return denied
    try:
        path = resolve_backup(filename)
        return FileResponse(path.open("rb"), as_attachment=True, filename=path.name, content_type="application/vnd.sqlite3")
    except BackupError as exc:
        return JsonResponse({"code": "NOT_FOUND", "message": str(exc)}, status=404)


@csrf_protect
@require_http_methods(["POST"])
def restore_database_backup(request):
    denied = _manager_or_error(request)
    if denied:
        return denied
    uploaded_path = None
    try:
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            confirmation = request.POST.get("confirmation")
            uploaded = request.FILES.get("backup_file")
            if not uploaded:
                raise BackupError("Vui lòng chọn tệp sao lưu.")
            source = uploaded_path = save_uploaded_backup(uploaded)
        else:
            payload = json.loads(request.body or b"{}")
            confirmation = payload.get("confirmation")
            source = resolve_backup(payload.get("filename", ""))
        if confirmation != "KHOI PHUC":
            raise BackupError("Cần xác nhận bằng cụm từ KHOI PHUC.")
        safety = restore_database(source)
        return JsonResponse({"status": "success", "message": "Khôi phục dữ liệu thành công. Hệ thống sẽ tải lại.", "safety_backup": safety.name})
    except (BackupError, json.JSONDecodeError) as exc:
        message = str(exc) if isinstance(exc, BackupError) else "Dữ liệu yêu cầu không hợp lệ."
        return JsonResponse({"code": "RESTORE_FAILED", "message": message}, status=400)
    finally:
        if uploaded_path:
            uploaded_path.unlink(missing_ok=True)
