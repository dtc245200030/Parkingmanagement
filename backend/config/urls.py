"""Cấu hình định tuyến URL trung tâm cho toàn bộ hệ thống parking_management."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="dashboard/index.html"), name="dashboard"),
    path("login/", TemplateView.as_view(template_name="authentication/login.html"), name="login-page"),
    path("health/", include("apps.core.urls")),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/vehicle-types/", include("apps.vehicles.urls")),
    path("api/vehicles/", include("apps.vehicles.urls")),
    path("api/parking-spots/", include("apps.parking.spot_urls")),
    path("api/pricing-rules/", include("apps.parking.pricing_urls")),
    path("api/parking/", include("apps.parking.urls")),
    path("api/tickets/", include("apps.tickets.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/ai/", include("apps.ai_assistant.urls")),
]
