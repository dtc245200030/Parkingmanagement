"""Cấu hình ASGI server cho dự án parking_management (hỗ trợ bất đồng bộ và async protocol)."""

import os
import sys
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
