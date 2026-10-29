# ParkAI Manager

Hệ thống quản lý bãi đỗ xe gồm REST API Django, giao diện dashboard và trợ lý AI dùng Google Gemini. Hệ thống hỗ trợ quản lý xe, khu vực/vị trí đỗ, bảng giá, lượt xe vào/ra, vé tháng, báo cáo và chatbot phân tích dữ liệu.

## Cấu trúc thư mục

```text
parking management/
├── backend/                         # REST API và nghiệp vụ Django
│   ├── apps/
│   │   ├── ai_assistant/            # Trợ lý AI và thu thập dữ liệu
│   │   ├── authentication/          # Đăng nhập, đăng xuất và session
│   │   ├── core/                    # Trang chủ, sao lưu và dữ liệu demo
│   │   ├── parking/                 # Khu vực, vị trí đỗ và bảng giá
│   │   ├── reports/                 # Thống kê và xuất báo cáo
│   │   ├── tickets/                 # Lượt gửi xe và vé tháng
│   │   ├── users/                   # Người dùng và phân quyền
│   │   └── vehicles/                # Phương tiện và loại xe
│   ├── config/                      # Settings, URL, WSGI và ASGI
│   ├── database/                    # Cơ sở dữ liệu cục bộ (không commit dữ liệu chạy)
│   ├── .env.example                 # Mẫu biến môi trường
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/                         # Ứng dụng Vue 3/Vite
│   │   ├── api/                     # API client
│   │   ├── components/              # Component dùng chung
│   │   ├── router/                  # Điều hướng Vue
│   │   └── views/                   # Các trang Vue
│   ├── templates/                   # Giao diện Django đang sử dụng
│   │   ├── authentication/          # Mẫu đăng nhập
│   │   └── dashboard/               # Dashboard chính
│   ├── static/                      # CSS và JavaScript dashboard
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── monitoring/
│   ├── grafana/                     # Dashboard và provisioning Grafana
│   ├── loki/                        # Cấu hình lưu trữ log
│   ├── prometheus/                  # Cấu hình thu thập metrics
│   └── promtail/                    # Cấu hình chuyển tiếp log
├── docker-compose.yml               # Điều phối ứng dụng và monitoring
├── docker-entrypoint.sh             # Migration và khởi động Django
├── Dockerfile                       # Image ứng dụng
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

### Chạy bằng Docker (khuyến nghị khi triển khai)

Yêu cầu Docker Desktop đang chạy. Sau khi clone repository, mở PowerShell tại thư mục gốc của dự án và tạo tệp môi trường từ mẫu:

```powershell
Copy-Item backend/.env.example backend/.env
```

Mở `backend/.env`, thay các giá trị bí mật và cấu hình `GEMINI_API_KEY` nếu dùng trợ lý AI. Sau đó kiểm tra cấu hình và khởi động toàn bộ hệ thống:

```powershell
docker compose --env-file backend/.env -f docker-compose.yml config
docker compose --env-file backend/.env -f docker-compose.yml up --build -d
docker compose --env-file backend/.env -f docker-compose.yml ps
```

Nạp dữ liệu demo trong lần chạy đầu (nếu cơ sở dữ liệu đang trống):

```powershell
docker compose --env-file backend/.env -f docker-compose.yml exec web python manage.py seed_demo
```

Dừng hệ thống bằng lệnh dưới đây. Dữ liệu SQLite, bản sao lưu, metrics, logs và cấu hình Grafana được giữ trong Docker volume:

```powershell
docker compose --env-file backend/.env -f docker-compose.yml down
```

Chỉ thêm tùy chọn `-v` khi thực sự muốn xóa toàn bộ dữ liệu của môi trường Docker.

#### Giám sát với Prometheus, Grafana và Loki

Lệnh Docker Compose phía trên khởi động ứng dụng cùng toàn bộ hệ thống quản trị và giám sát:

| Dịch vụ | Địa chỉ | Mục đích |
|---|---|---|
| ParkAI | <http://localhost:8000/> | Ứng dụng chính |
| SQLite Web | <http://localhost:8081/> | Quản trị cơ sở dữ liệu SQLite |
| Django metrics | <http://localhost:8000/metrics> | Số liệu thô của ứng dụng |
| Prometheus | <http://localhost:9090/> | Thu thập và truy vấn metrics |
| Grafana | <http://localhost:3000/> | Dashboard metrics và logs |
| Loki | <http://localhost:3100/ready> | Lưu trữ nhật ký |
| Promtail | <http://localhost:9080/ready> | Thu thập log Docker và gửi tới Loki |
| Node Exporter | <http://localhost:9100/metrics> | CPU, RAM, ổ đĩa và mạng của Docker Linux VM |
| cAdvisor | <http://localhost:8080/> | CPU, RAM, mạng và trạng thái từng container |

Grafana tự động có sẵn hai nguồn dữ liệu `Prometheus`, `Loki` và hai dashboard **ParkAI - Tổng quan hệ thống**, **ParkAI - Hạ tầng và Container** trong thư mục **ParkAI**. Tài khoản được lấy từ `backend/.env` qua `GRAFANA_ADMIN_USER` và `GRAFANA_ADMIN_PASSWORD`; hãy đổi mật khẩu mẫu trước khi triển khai công khai.

SQLite Web dùng mật khẩu trong biến `SQLITE_WEB_PASSWORD` của `backend/.env`. Công cụ này có thể thêm, sửa và xóa dữ liệu trực tiếp, vì vậy chỉ nên mở cổng 8081 trong môi trường nội bộ và cần tạo bản sao lưu trước các thay đổi quan trọng.

Kiểm tra Prometheus đã thu thập dữ liệu: mở **Status → Target health** tại Prometheus và xác nhận các job `parkai-django`, `node-exporter`, `cadvisor`, `prometheus` có trạng thái `UP`. Để xem log trong Grafana, mở dashboard ParkAI hoặc vào **Explore**, chọn nguồn `Loki` và truy vấn:

```logql
{application="parkai"}
```

Một số lệnh xử lý sự cố thường dùng:

```powershell
docker compose --env-file backend/.env -f docker-compose.yml ps
docker compose --env-file backend/.env -f docker-compose.yml logs -f web sqlite-web prometheus grafana loki promtail node-exporter cadvisor
docker compose --env-file backend/.env -f docker-compose.yml restart web sqlite-web prometheus grafana loki promtail node-exporter cadvisor
```

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
