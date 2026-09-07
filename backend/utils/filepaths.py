import os
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCANS_DIR = os.path.join(ROOT_DIR, "scans")
BACKUP_DIR = os.path.join(ROOT_DIR, "backup")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)


def get_today_scan_dir() -> str:
    d = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(SCANS_DIR, d)


def slugify_guest_name(first_name: str | None, last_name: str | None) -> str:
    name = " ".join([n for n in [first_name or "", last_name or ""] if n]).strip() or "unknown"
    return (
        name.lower().replace(" ", "_").replace("/", "-").replace("\\", "-").replace("|", "-")
    )


def get_image_path(dir_path: str, guest_name_slug: str, side: str, encrypted: bool = True) -> str:
    base = f"{guest_name_slug}_{side}.jpg"
    if encrypted:
        base += ".enc"
    return os.path.join(dir_path, base)


def get_temp_image_path(side: str) -> str:
    return os.path.join(TEMP_DIR, f"temp_{side}_{datetime.now().timestamp()}.jpg")


def get_temp_encrypted_image_path(side: str) -> str:
    return os.path.join(TEMP_DIR, f"temp_{side}_{datetime.now().timestamp()}.jpg.enc")