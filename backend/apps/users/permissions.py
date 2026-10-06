"""Lớp định nghĩa phân quyền truy cập API REST cho người dùng hệ thống."""

from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Quyền truy cập dành riêng cho Quản lý hệ thống (QuanLy, manager, admin)."""

    def has_permission(self, request, view):
        """Kiểm tra vai trò người dùng có thuộc nhóm quản trị hay không."""
        role = getattr(request, "user_role", None) or request.headers.get("X-User-Role")
        return role in ["QuanLy", "manager", "admin"]


class IsStaffOrAdmin(permissions.BasePermission):
    """Quyền truy cập dành cho Nhân viên hoặc Quản lý."""

    def has_permission(self, request, view):
        """Cho phép truy cập các API dành cho nhân viên hệ thống."""
        return True

