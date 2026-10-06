"""
Django Test Case cho module AI Assistant.
Chạy với: python manage.py test apps.ai_assistant

Lưu ý:
- Các test validation không cần Gemini API thật.
- Test data_collector và calculate_fee chạy độc lập với DB test (SQLite in-memory).
- View-level tests dùng mock để không cần API key thật.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client


class AIChatViewValidationTests(TestCase):
    """Kiểm thử xác thực đầu vào cho AIChatView (không gọi Gemini thực tế)."""

    def setUp(self):
        self.client = Client()
        self.url = "/api/ai/chat/"
        # Mock get_ai_response để không gọi Gemini thực tế
        self.patcher = patch(
            "apps.ai_assistant.views.get_ai_response",
            return_value="AI mock response cho kiểm thử"
        )
        self.mock_ai = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    # ------------------------------------------------------------------
    # TC_AI_001: GET endpoint trả về trạng thái sẵn sàng
    # ------------------------------------------------------------------
    def test_tc_ai_001_get_returns_status(self):
        """TC_AI_001: GET /api/ai/chat/ → HTTP 200 + status sẵn sàng."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("endpoint", data)
        self.assertIn("body", data)

    # ------------------------------------------------------------------
    # TC_AI_008: Message rỗng → 400
    # ------------------------------------------------------------------
    def test_tc_ai_008_empty_message_returns_400(self):
        """TC_AI_008: POST với message="" → HTTP 400 + error."""
        resp = self.client.post(
            self.url,
            data=json.dumps({"message": "", "history": []}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("error", data)
        self.assertIn("trong", data["error"].lower())  # "khong duoc de trong"

    # ------------------------------------------------------------------
    # TC_AI_009: Message chỉ khoảng trắng → 400
    # ------------------------------------------------------------------
    def test_tc_ai_009_whitespace_message_returns_400(self):
        """TC_AI_009: POST với message="   " → HTTP 400."""
        resp = self.client.post(
            self.url,
            data=json.dumps({"message": "      ", "history": []}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("error", data)

    # ------------------------------------------------------------------
    # TC_AI_010: Body không phải JSON → 400
    # ------------------------------------------------------------------
    def test_tc_ai_010_invalid_json_returns_400(self):
        """TC_AI_010: POST với body không phải JSON → HTTP 400."""
        resp = self.client.post(
            self.url,
            data=b"this_is_not_json",
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("error", data)

    # ------------------------------------------------------------------
    # TC_AI_011: Message > 1000 ký tự → 400
    # ------------------------------------------------------------------
    def test_tc_ai_011_message_over_1000_returns_400(self):
        """TC_AI_011: POST với message dài 1001 ký tự → HTTP 400 + thông báo 1000."""
        resp = self.client.post(
            self.url,
            data=json.dumps({"message": "A" * 1001, "history": []}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("error", data)
        self.assertIn("1000", data["error"])

    # ------------------------------------------------------------------
    # TC_AI_016: Message đúng 1000 ký tự không bị validation từ chối
    # ------------------------------------------------------------------
    def test_tc_ai_016_message_exactly_1000_not_rejected_by_validation(self):
        """TC_AI_016: POST với message đúng 1000 ký tự → không bị 400 validation."""
        resp = self.client.post(
            self.url,
            data=json.dumps({"message": "A" * 1000, "history": []}),
            content_type="application/json"
        )
        # Không phải 400 (validation từ chối). Có thể 200 hoặc 500 nếu AI key lỗi.
        self.assertNotEqual(resp.status_code, 400,
                            msg="Message 1000 ký tự không được bị validation từ chối")

    # ------------------------------------------------------------------
    # TC_AI_017: Message đúng 1001 ký tự bị từ chối
    # ------------------------------------------------------------------
    def test_tc_ai_017_message_1001_chars_rejected(self):
        """TC_AI_017: POST với message 1001 ký tự → HTTP 400 (vượt biên)."""
        resp = self.client.post(
            self.url,
            data=json.dumps({"message": "A" * 1001, "history": []}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # TC_AI_013: History không phải list → xử lý an toàn (không 500)
    # ------------------------------------------------------------------
    def test_tc_ai_013_invalid_history_no_crash(self):
        """TC_AI_013: History không phải list → không bị lỗi 500."""
        resp = self.client.post(
            self.url,
            data=json.dumps({"message": "Bãi xe có bao nhiêu khu vực?", "history": "invalid"}),
            content_type="application/json"
        )
        # Chấp nhận 200 (bỏ qua history sai) hoặc 400 (báo lỗi)
        self.assertIn(resp.status_code, [200, 400],
                      msg=f"Không mong đợi HTTP {resp.status_code} khi history sai")
        self.assertNotEqual(resp.status_code, 500, "Không được crash 500")

    # ------------------------------------------------------------------
    # TC_AI_014: PUT method → không phải 200
    # ------------------------------------------------------------------
    def test_tc_ai_014_put_method_not_allowed(self):
        """TC_AI_014: PUT /api/ai/chat/ → HTTP 405 hoặc 400."""
        resp = self.client.put(
            self.url,
            data=json.dumps({"message": "test"}),
            content_type="application/json"
        )
        self.assertIn(resp.status_code, [405, 400, 403],
                      msg=f"PUT phải trả về 405/400/403, nhận được {resp.status_code}")


class AIDataCollectorTests(TestCase):
    """Kiểm thử module data_collector."""

    def test_tc_ai_021_collect_context_returns_correct_structure(self):
        """TC_AI_021: collect_db_context() → dict đúng cấu trúc."""
        from apps.ai_assistant.data_collector import collect_db_context
        result = collect_db_context()

        # Kiểm tra type
        self.assertIsInstance(result, dict)

        # Kiểm tra 2 key chính
        self.assertIn("context_text", result)
        self.assertIn("summary", result)

        # context_text phải là chuỗi không rỗng
        self.assertIsInstance(result["context_text"], str)
        self.assertGreater(len(result["context_text"]), 50)

    def test_tc_ai_021_summary_required_keys(self):
        """TC_AI_021: summary phải có đủ 9 key."""
        from apps.ai_assistant.data_collector import collect_db_context
        summary = collect_db_context()["summary"]

        required = [
            "total_capacity", "total_in_lot", "total_available",
            "occupancy_rate", "total_revenue", "total_all_sessions",
            "peak_hour", "peak_hour_count", "monthly_active"
        ]
        for key in required:
            self.assertIn(key, summary, f"Thiếu key '{key}' trong summary")

    def test_tc_ai_021_summary_values_non_negative(self):
        """TC_AI_021: Tất cả giá trị số trong summary phải >= 0."""
        from apps.ai_assistant.data_collector import collect_db_context
        summary = collect_db_context()["summary"]

        numeric_keys = [
            "total_capacity", "total_in_lot", "total_available",
            "occupancy_rate", "total_revenue", "total_all_sessions", "monthly_active"
        ]
        for key in numeric_keys:
            self.assertGreaterEqual(summary[key], 0,
                                    f"summary['{key}'] = {summary[key]} không được âm")

    def test_tc_ai_021_peak_hour_valid_range(self):
        """TC_AI_021e: peak_hour phải trong [0, 23]."""
        from apps.ai_assistant.data_collector import collect_db_context
        summary = collect_db_context()["summary"]
        peak = summary["peak_hour"]
        self.assertGreaterEqual(peak, 0, "peak_hour >= 0")
        self.assertLessEqual(peak, 23, "peak_hour <= 23")

    def test_tc_ai_021_occupancy_rate_range(self):
        """TC_AI_021f: occupancy_rate phải trong [0, 100]."""
        from apps.ai_assistant.data_collector import collect_db_context
        summary = collect_db_context()["summary"]
        rate = summary["occupancy_rate"]
        self.assertGreaterEqual(rate, 0.0, "occupancy_rate >= 0")
        self.assertLessEqual(rate, 100.0, "occupancy_rate <= 100")

    def test_tc_ai_021_context_contains_required_sections(self):
        """TC_AI_021g: context_text phải chứa các section tiêu đề đúng."""
        from apps.ai_assistant.data_collector import collect_db_context
        ctx = collect_db_context()["context_text"]

        required_sections = [
            "TRẠNG THÁI BÃI ĐỖ XE",
            "TỔNG HỢP LƯỢT XE",
            "DOANH THU",
            "VÉ THÁNG",
            "BẢNG GIÁ",
        ]
        for section in required_sections:
            self.assertIn(section, ctx, f"context_text thiếu section: '{section}'")


class AICalculateFeeTests(TestCase):
    """Kiểm thử hàm calculate_fee."""

    def test_tc_ai_022_zero_duration_non_negative(self):
        """TC_AI_022: Thời gian gửi = 0 giây → phí không âm."""
        from apps.tickets.services import calculate_fee
        from django.utils import timezone
        now = timezone.now()
        fee = calculate_fee(loai_xe=None, thoi_gian_vao=now, thoi_gian_ra=now)
        self.assertGreaterEqual(fee, 0, "Phí gửi xe không được âm")

    def test_monthly_ticket_fee_is_zero(self):
        """Vé tháng → phí = 0."""
        from apps.tickets.services import calculate_fee
        from django.utils import timezone
        now = timezone.now()
        fee = calculate_fee(loai_xe=None, thoi_gian_vao=now, is_monthly=True)
        from decimal import Decimal
        self.assertEqual(fee, Decimal("0.00"), "Phí vé tháng phải = 0")

    def test_fee_increases_with_duration(self):
        """Phí tăng khi thời gian gửi xe tăng (với loại xe mặc định)."""
        from apps.tickets.services import calculate_fee
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        fee_1h = calculate_fee(loai_xe=None,
                               thoi_gian_vao=now - timedelta(hours=1),
                               thoi_gian_ra=now)
        fee_3h = calculate_fee(loai_xe=None,
                               thoi_gian_vao=now - timedelta(hours=3),
                               thoi_gian_ra=now)
        self.assertGreaterEqual(fee_3h, fee_1h,
                                f"Phí 3h ({fee_3h}) phải >= phí 1h ({fee_1h})")

    def test_fee_no_exception_with_none_loai_xe(self):
        """Hàm calculate_fee không ném ngoại lệ khi loai_xe=None."""
        from apps.tickets.services import calculate_fee
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        try:
            fee = calculate_fee(loai_xe=None,
                                thoi_gian_vao=now - timedelta(hours=2),
                                thoi_gian_ra=now)
            self.assertGreaterEqual(fee, 0)
        except Exception as e:
            self.fail(f"calculate_fee ném ngoại lệ không mong muốn: {e}")
