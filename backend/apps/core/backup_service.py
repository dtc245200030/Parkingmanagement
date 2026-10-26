"""SQLite backup and restore service for ParkAI."""

import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import connections
from django.utils import timezone

BACKUP_NAME_RE = re.compile(r"^parkai_(?:backup|pre_restore)_\d{8}_\d{6}_[0-9a-f]{8}\.sqlite3$")
REQUIRED_TABLES = {"django_migrations", "NguoiDung", "KhuVuc", "LuotGuiXe"}


class BackupError(Exception):
    """A safe-to-display backup/restore error."""


def database_path():
    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.sqlite3" or config["NAME"] == ":memory:":
        raise BackupError("Chức năng này hiện chỉ hỗ trợ cơ sở dữ liệu SQLite.")
    return Path(config["NAME"]).resolve()


def backup_directory():
    folder = Path(getattr(settings, "BACKUP_DIR", settings.BASE_DIR / "backups")).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _new_name(prefix):
    timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    return f"parkai_{prefix}_{timestamp}_{uuid4().hex[:8]}.sqlite3"


def validate_sqlite(path):
    try:
        db = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        try:
            integrity = db.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise BackupError("Tệp sao lưu bị lỗi toàn vẹn dữ liệu.")
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            db.close()
    except (sqlite3.DatabaseError, OSError) as exc:
        raise BackupError("Tệp được chọn không phải cơ sở dữ liệu SQLite hợp lệ.") from exc
    if REQUIRED_TABLES - tables:
        raise BackupError("Tệp sao lưu không đúng cấu trúc dữ liệu ParkAI.")


def create_backup(prefix="backup"):
    source_path = database_path()
    if not source_path.exists():
        raise BackupError("Không tìm thấy cơ sở dữ liệu để sao lưu.")
    target = backup_directory() / _new_name(prefix)
    temporary = target.with_suffix(".tmp")
    try:
        source = sqlite3.connect(str(source_path), timeout=30)
        destination = sqlite3.connect(str(temporary))
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        validate_sqlite(temporary)
        os.replace(temporary, target)
        return target
    except BackupError:
        temporary.unlink(missing_ok=True)
        raise
    except (sqlite3.DatabaseError, OSError) as exc:
        temporary.unlink(missing_ok=True)
        raise BackupError("Không thể tạo bản sao lưu lúc này.") from exc


def list_backups():
    result = []
    for path in backup_directory().glob("parkai_*.sqlite3"):
        if not BACKUP_NAME_RE.fullmatch(path.name):
            continue
        stat = path.stat()
        result.append({
            "filename": path.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone()).isoformat(),
            "is_safety_backup": path.name.startswith("parkai_pre_restore_"),
        })
    return sorted(result, key=lambda item: item["created_at"], reverse=True)


def resolve_backup(filename):
    if not BACKUP_NAME_RE.fullmatch(filename or ""):
        raise BackupError("Tên tệp sao lưu không hợp lệ.")
    folder = backup_directory()
    path = (folder / filename).resolve()
    if path.parent != folder or not path.is_file():
        raise BackupError("Không tìm thấy tệp sao lưu.")
    return path


def save_uploaded_backup(uploaded_file, max_bytes=100 * 1024 * 1024):
    if uploaded_file.size > max_bytes:
        raise BackupError("Tệp sao lưu vượt quá giới hạn 100 MB.")
    descriptor, name = tempfile.mkstemp(prefix="parkai_upload_", suffix=".sqlite3", dir=backup_directory())
    os.close(descriptor)
    path = Path(name)
    try:
        with path.open("wb") as output:
            for chunk in uploaded_file.chunks():
                output.write(chunk)
        validate_sqlite(path)
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def restore_database(source):
    validate_sqlite(source)
    safety_backup = create_backup(prefix="pre_restore")
    target = database_path()
    temporary = target.with_name(f".{target.name}.restore-{uuid4().hex}.tmp")
    try:
        shutil.copy2(source, temporary)
        validate_sqlite(temporary)
        connections.close_all()
        os.replace(temporary, target)
    except (OSError, sqlite3.DatabaseError) as exc:
        temporary.unlink(missing_ok=True)
        raise BackupError("Không thể thay thế cơ sở dữ liệu. Dữ liệu hiện tại vẫn được giữ nguyên.") from exc
    return safety_backup
