"""Giao tiep voi Google Gemini API."""

import os
import google.generativeai as genai

_SYSTEM_PROMPT = """
Ban la tro ly AI thong minh chuyen phan tich du lieu cho he thong quan ly bai gui xe "ParkAI Manager".
Ban duoc cung cap du lieu thuc te tu co so du lieu cua he thong (luot gui xe, doanh thu, khu vuc, ve thang, bang gia).

Nhiem vu cua ban:
1. Tra loi chinh xac cac cau hoi ve tinh trang hien tai cua bai gui xe
2. Phan tich xu huong doanh thu va luot xe
3. Du doan gio cao diem va goi y bo tri nhan su
4. Dua ra cac khuyen nghi thuc te de nang cao hieu qua van hanh
5. Tinh toan va giai thich so lieu mot cach ro rang

Quy tac:
- Luon tra loi bang tieng Viet, giao tiep than thien va chuyen nghiep
- Chi su dung du lieu duoc cung cap, khong bịa dat so lieu
- Neu so lieu cu the khi can (VND, phan tram, so luong)
- Goi y hanh dong thuc te khi phu hop
- Neu du lieu khong du, hay noi ro cho nguoi dung biet
"""

def get_ai_response(user_message: str, db_context: str, chat_history: list = None) -> str:
    """
    Goi Gemini API voi context tu Database.

    Args:
        user_message: Cau hoi cua nguoi dung
        db_context: Du lieu tong hop tu Django ORM
        chat_history: Lich su hoi thoai truoc do (list of dict {role, content})

    Returns:
        Phan hoi cua AI (str)
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return "Loi: Chua cau hinh GEMINI_API_KEY. Vui long them API key vao file .env."

    try:
        genai.configure(api_key=api_key)
        
        # Thử lần lượt các model phổ biến
        candidate_models = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]
        model = None
        for m_name in candidate_models:
            try:
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=_SYSTEM_PROMPT,
                )
                break
            except Exception:
                continue

        if not model:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=_SYSTEM_PROMPT,
            )

        # Xay dung noi dung hoi thoai
        history_parts = []
        if chat_history:
            for msg in chat_history[-6:]:  # Giu toi da 6 turns gan nhat
                role = "user" if msg.get("role") == "user" else "model"
                history_parts.append({"role": role, "parts": [msg.get("content", "")]})

        # Prompt chinh: Du lieu DB + Cau hoi nguoi dung
        full_prompt = f"""
{db_context}

=== CAU HOI CUA NGUOI DUNG ===
{user_message}
"""

        if history_parts:
            chat = model.start_chat(history=history_parts)
            response = chat.send_message(full_prompt)
        else:
            response = model.generate_content(full_prompt)

        return response.text

    except Exception as exc:
        error_msg = str(exc)
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            return "Loi: API Key khong hop le. Vui long kiem tra lai GEMINI_API_KEY trong file .env."
        if "quota" in error_msg.lower():
            return "Loi: Da vuot qua gioi han API Gemini mien phi. Vui long thu lai sau."
        return f"Loi ket noi Gemini API: {error_msg}"
