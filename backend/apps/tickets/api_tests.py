"""Các unit test cho API endpoint check-in và thống kê vé."""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.parking.models import ParkingSpot, PricingRule
from apps.tickets.models import ParkingTicket
from apps.vehicles.models import VehicleType


class TicketApiTests(TestCase):
    """Bộ kiểm thử cho các endpoint API của vé xe."""

    def setUp(self):
        """Khởi tạo APIClient cho kiểm thử."""
        self.client = APIClient()

    def test_check_in_endpoint(self):
        """Kiểm tra gọi API check-in qua POST /api/tickets/check-in/."""
        response = self.client.post("/api/tickets/check-in/", {
            "plate_number": "29A-12345",
            "vehicle_type": "XeMay",
            "zone": "Khu A",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "success")

    def test_summary_endpoint(self):
        """Kiểm tra gọi API tổng quan qua GET /api/reports/summary/."""
        response = self.client.get("/api/reports/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_in_lot", response.json())

