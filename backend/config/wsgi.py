"""Cấu hình WSGI server phục vụ deployment ứng dụng web parking_management."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
