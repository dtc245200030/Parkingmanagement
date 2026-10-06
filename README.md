# ParkAI Manager

Hệ thống quản lý bãi đỗ xe gồm REST API Django, giao diện dashboard và trợ lý AI dùng Google Gemini. Hệ thống hỗ trợ quản lý xe, khu vực/vị trí đỗ, bảng giá, lượt xe vào/ra, vé tháng, báo cáo và chatbot phân tích dữ liệu.

## Cấu trúc thư mục

```text
parking management/
├── backend/
│   ├── apps/                 # Các Django app nghiệp vụ
│   ├── config/               # Settings, URL, WSGI/ASGI
│   ├── database/             # Cơ sở dữ liệu SQLite cục bộ
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/                  # Ứng dụng Vue 3/Vite
│   ├── templates/            # Dashboard Django hiện tại
│   ├── static/               # CSS/JavaScript của dashboard Django
│   ├── index.html
│   └── package.json
└── README.md
```

Backend tự tìm `templates/` và `static/` trong `frontend/`. Vue là frontend SPA riêng, chạy ở cổng 3000 và proxy các request `/api` sang Django ở cổng 8000.

## Yêu cầu

- Python 3.10 trở lên
- Node.js 18 trở lên
- npm hoặc pnpm
- SQLite (mặc định); có thể cấu hình hệ quản trị khác qua `.env`

## Cài đặt backend

Chạy từ thư mục gốc của dự án bằng PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt

Copy-Item backend\.env.example backend\.env
```

Nếu PowerShell chặn script kích hoạt, có thể gọi trực tiếp `.\.venv\Scripts\python.exe` trong các lệnh bên dưới.

Mở `backend/.env` và cấu hình:

```dotenv
DJANGO_SECRET_KEY=thay-bang-chuoi-bi-mat
DJANGO_DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=database/db.sqlite3
GEMINI_API_KEY=
```

`GEMINI_API_KEY` chỉ bắt buộc khi dùng chatbot AI. Không commit file `.env` hoặc API key thật lên Git.

Khởi tạo cơ sở dữ liệu và nạp dữ liệu demo:

```powershell
Set-Location backend
python manage.py migrate
python manage.py seed_demo
```

Dữ liệu demo có các tài khoản:

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Quản lý | `admin` | `admin123` |
| Nhân viên | `mai` | `123456` |
| Nhân viên | `hung` | `123456` |

Các tài khoản trên chỉ dùng cho môi trường demo/local.

## Chạy hệ thống

### Dashboard Django

```powershell
Set-Location backend
python manage.py runserver
```

Truy cập:

- Dashboard: <http://127.0.0.1:8000/>
- Trang đăng nhập: <http://127.0.0.1:8000/login/>
- Django Admin: <http://127.0.0.1:8000/admin/>
- Health check: <http://127.0.0.1:8000/health/>

### Frontend Vue/Vite

Mở terminal thứ hai tại thư mục gốc:

```powershell
Set-Location frontend
npm install
npm run dev
```

Hoặc dùng pnpm:

```powershell
Set-Location frontend
pnpm install
pnpm run dev
```

Truy cập <http://127.0.0.1:3000/>. Backend phải đang chạy ở `127.0.0.1:8000` để proxy API hoạt động.

Build frontend production:

```powershell
Set-Location frontend
npm run build
```

Kết quả build nằm trong `frontend/dist/`.

## API chính

| Nhóm | Endpoint tiêu biểu |
|---|---|
| Xác thực | `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/` |
| Người dùng | `/api/users/` |
| Loại xe và phương tiện | `/api/vehicle-types/`, `/api/vehicles/` |
| Bãi đỗ và bảng giá | `/api/parking-spots/`, `/api/pricing-rules/` |
| Lượt xe/vé | `/api/tickets/`, `/api/tickets/check-in/`, `/api/tickets/check-out/` |
| Báo cáo | `/api/reports/summary/`, `/api/reports/charts/`, `/api/reports/export/excel/` |
| Trợ lý AI | `GET/POST /api/ai/chat/` |

## Kiểm thử

Backend:

```powershell
Set-Location backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Chạy riêng test AI (test dùng mock, không tiêu tốn Gemini API):

```powershell
python manage.py test apps.ai_assistant.tests_ai
```

Frontend:

```powershell
Set-Location frontend
npm run build
```

## Kết quả kiểm tra gần nhất

Ngày 03/10/2026, dự án đã được kiểm tra sau khi tách lại `backend/` và `frontend/`:

- `python manage.py check`: không phát hiện lỗi.
- `python manage.py makemigrations --check --dry-run`: không có thay đổi model chưa tạo migration.
- `python manage.py test`: 32/32 test thành công.
- `python manage.py migrate --noinput`: không có migration chưa áp dụng.
- Django development server: khởi động thành công tại `127.0.0.1:8000`.
- `pnpm run build`: Vue/Vite build thành công.

Lưu ý: package `google-generativeai` hiện phát cảnh báo ngừng được Google hỗ trợ. Hệ thống vẫn chạy và test thành công, nhưng nên lên kế hoạch chuyển module AI sang SDK `google-genai`.

## Xử lý lỗi thường gặp

- `python is not recognized`: cài Python và chọn **Add Python to PATH**, sau đó mở terminal mới.
- `No module named django`: kích hoạt `.venv` và cài lại `backend/requirements.txt`.
- `unable to open database file`: dùng `DB_NAME=database/db.sqlite3`; đường dẫn tương đối được tính từ `backend/`.
- Frontend không gọi được API: kiểm tra Django đang chạy đúng cổng 8000.
- Chatbot báo chưa cấu hình key: thêm `GEMINI_API_KEY` hợp lệ vào `backend/.env`, sau đó khởi động lại backend.
