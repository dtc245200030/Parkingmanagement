"""Định tuyến các đường dẫn API cho vé xe, lượt gửi xe, check-in, check-out và vé tháng."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.tickets.views import (
    LuotGuiXeViewSet,
    VeThangViewSet,
    VeXeViewSet,
    check_in_api,
    check_out_api,
)

router = DefaultRouter()
router.register(r"cards", VeXeViewSet, basename="vexe")
router.register(r"monthly", VeThangViewSet, basename="vethang")
router.register(r"sessions", LuotGuiXeViewSet, basename="luotguixe")
router.register(r"", LuotGuiXeViewSet, basename="luotguixe-default")

urlpatterns = [
    path("check-in/", check_in_api, name="tickets-check-in"),
    path("check-out/", check_out_api, name="tickets-check-out"),
    path("in-lot/", LuotGuiXeViewSet.as_view({"get": "in_lot"}), name="tickets-in-lot"),
    path("", include(router.urls)),
]

