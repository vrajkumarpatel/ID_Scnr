import os
import json
import csv
from datetime import datetime
from typing import Dict
from .models import Guest


SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")


def _load_settings() -> Dict:
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "pms_export_mode": "json",
            "pms_export_path": os.path.join(os.path.dirname(__file__), "data", "pms_exports"),
            "pms_api_url": "http://localhost:9999/pms-sync",
        }


def _payload(guest: Guest) -> Dict:
    return {
        "id": guest.id,
        "first_name": guest.first_name,
        "middle_name": guest.middle_name,
        "last_name": guest.last_name,
        "dob": guest.dob,
        "id_number": guest.id_number,
        "expiration_date": guest.expiration_date,
        "issue_date": guest.issue_date,
        "address": guest.address,
        "city": guest.city,
        "state": guest.state,
        "zip_code": guest.zip_code,
        "nationality": guest.nationality,
        "phone_country_code": guest.phone_country_code,
        "phone_number": guest.phone_number,
        "room_number": guest.room_number,
        "remarks": guest.remarks,
        "image_front_path": guest.image_front_path,
        "image_back_path": guest.image_back_path,
        "exported_at": datetime.utcnow().isoformat(),
    }


def write_guest_to_pms(guest: Guest) -> str:
    """Export guest to PMS in mode configured by settings: JSON, CSV, or API POST."""
    s = _load_settings()
    mode = s.get("pms_export_mode", "json")
    export_dir = s.get("pms_export_path") or os.path.join(os.path.dirname(__file__), "data", "pms_exports")
    os.makedirs(export_dir, exist_ok=True)
    payload = _payload(guest)

    if mode == "csv":
        fname = f"guest_{guest.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fpath = os.path.join(export_dir, fname)
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(payload.keys()))
            writer.writeheader()
            writer.writerow(payload)
        return fpath
    elif mode == "api":
        # Dummy API POST using standard library
        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(s.get("pms_api_url", "http://localhost:9999/pms-sync"),
                                         data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            # Also persist a local receipt
            fname = f"guest_{guest.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.api.json"
            fpath = os.path.join(export_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump({"status": "posted", "payload": payload}, f, indent=2)
            return fpath
        except Exception as e:
            fname = f"guest_{guest.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.api_error.json"
            fpath = os.path.join(export_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump({"status": "error", "error": str(e), "payload": payload}, f, indent=2)
            return fpath
    else:
        # Default JSON
        fname = f"guest_{guest.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fpath = os.path.join(export_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return fpath