"""API Views cho module AI Assistant."""

import json
import logging

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .data_collector import collect_db_context
from .gemini_client import get_ai_response

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class AIChatView(View):
    """
    POST /api/ai/chat
    Body: { "message": "...", "history": [...] }
    Response: { "reply": "...", "summary": {...} }
    """

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Du lieu JSON khong hop le."}, status=400)

        user_message = body.get("message", "").strip()
        chat_history = body.get("history", [])

        if not user_message:
            return JsonResponse({"error": "Cau hoi khong duoc de trong."}, status=400)

        if len(user_message) > 1000:
            return JsonResponse({"error": "Cau hoi qua dai (toi da 1000 ky tu)."}, status=400)

        try:
            # 1. Thu thap du lieu tu DB
            db_data = collect_db_context()
            db_context = db_data["context_text"]
            summary = db_data["summary"]

            # 2. Goi Gemini API
            ai_reply = get_ai_response(
                user_message=user_message,
                db_context=db_context,
                chat_history=chat_history,
            )

            return JsonResponse({
                "reply": ai_reply,
                "summary": summary,
            })

        except Exception as exc:
            logger.error("AI Chat error: %s", exc, exc_info=True)
            return JsonResponse({"error": f"Loi he thong: {str(exc)}"}, status=500)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "status": "AI Assistant san sang",
            "endpoint": "POST /api/ai/chat",
            "body": {"message": "cau hoi cua ban", "history": []},
        })
