from fastapi import FastAPI, Form, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import re
from datetime import datetime, timezone
import io
import os
import json
import asyncio
import base64
import time
import logging
import sqlite3
from PIL import Image

from .database import SessionLocal, init_db
from . import models, schemas
from .utils import filepaths
from .utils.scanner_interface import list_devices as list_scan_devices
from .utils.scanner_interface import capture_duplex as scan_capture_duplex
from .utils.date_utils import (
    normalize_date_to_iso,
    iso_to_us_date,
    parse_iso_date,
    validate_date_range
)
from .ocr_utils import extract_structured_data
from .security import decrypt_bytes, encrypt_bytes, ensure_keys_initialized, verify_pin, update_pin
from .dnr_manager import check_dnr_match, verify_admin_pin
from .pms_writer import write_guest_to_pms
from .auth import create_jwt, verify_jwt, get_bearer_token


app = FastAPI(title="IDscnr — by Vraj", version="0.1.0")

# Settings persistence
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")


def load_settings():
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "cors_origins": ["http://localhost:5173"],
            "ocr_provider": "tesseract",
            "google_api_key": None,
            "scan_device": None,
            "auto_pms_write": False,
            "dark_mode": True,
            "pms_export_mode": "json",
            "pms_export_path": os.path.join(os.path.dirname(__file__), "data", "pms_exports"),
            "pms_api_url": "http://localhost:9999/pms-sync",
            "jwt_secret": "dev-secret-change-me",
            "pms_window_title": "PMS",
            "pms_autofill_tab_order": [
                "first_name","last_name","dob","address","city","state","zip_code","phone_number","room_number"
            ],
            "pms_autofill_delay_ms": 50,
        }


def save_settings(s: dict):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(s, f, indent=2)


_settings = load_settings()
_jwt_secret_env = os.environ.get("JWT_SECRET")
try:
    env_api_key = os.environ.get("GOOGLE_VISION_API_KEY")
    if env_api_key:
        _settings["google_api_key"] = env_api_key
    env_provider = os.environ.get("OCR_PROVIDER")
    if env_provider in {"tesseract", "google"}:
        _settings["ocr_provider"] = env_provider
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.get("cors_origins", ["http://localhost:5173"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Initialize DB and encryption keys
    ensure_keys_initialized()
    init_db()
    # Create base folders
    os.makedirs(filepaths.SCANS_DIR, exist_ok=True)
    os.makedirs(filepaths.BACKUP_DIR, exist_ok=True)
    # Ensure settings file exists
    try:
        if not os.path.exists(SETTINGS_PATH):
            save_settings(_settings)
    except Exception:
        pass

    # Initialize app logger
    import logging, json as _json
    log_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'app.log')
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler()])
    logging.info(_json.dumps({"event": "startup", "ts": datetime.now(timezone.utc).isoformat()}))

    # Lightweight index migrations
    try:
        from .database import engine
        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_guests_id_number ON guests(id_number)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_guests_name_dob ON guests(first_name, last_name, dob)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_guests_created_at ON guests(created_at)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_blacklist_id_number ON blacklist(id_number)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_blacklist_name_dob ON blacklist(first_name, last_name, dob)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_blacklist_norm_name_dob ON blacklist(first_name_norm, last_name_norm, dob_iso)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_blacklist_norm_id ON blacklist(id_number_norm)")
            # Legacy import: migrate blacklist entries from older DB if found
            try:
                root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                legacy_db = os.path.join(root, 'backend', 'data', 'guestdb.sqlite')
                if os.path.exists(legacy_db):
                    lx = sqlite3.connect(legacy_db)
                    try:
                        rows = lx.execute("SELECT first_name,last_name,dob,id_number,notes,created_at FROM blacklist").fetchall()
                        for r in rows:
                            fn, ln, dob, idn, notes, created_at = r
                            # Insert if not exists by id_number or by normalized name+dob
                            conn.exec_driver_sql(
                                "INSERT INTO blacklist (first_name,last_name,dob,id_number,notes,created_at,first_name_norm,last_name_norm,dob_iso,id_number_norm)\n                                 SELECT :fn,:ln,:dob,:idn,:notes,:ca,:fnn,:lnn,:dobi,:inn\n                                 WHERE NOT EXISTS (\n                                   SELECT 1 FROM blacklist b\n                                   WHERE (b.id_number = :idn AND :idn IS NOT NULL)\n                                      OR (b.first_name_norm = :fnn AND b.last_name_norm = :lnn AND b.dob_iso = :dobi)\n                                 )",
                                {
                                    'fn': fn, 'ln': ln, 'dob': dob, 'idn': idn, 'notes': notes,
                                    'ca': created_at,
                                    'fnn': (fn or '').lower() if fn else None,
                                    'lnn': (ln or '').lower() if ln else None,
                                    'dobi': dob,
                                    'inn': (idn or '').upper() if idn else None,
                                }
                            )
                    finally:
                        lx.close()
            except Exception:
                pass
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


## Removed legacy /scan/save endpoint


from fastapi import Query
from datetime import datetime as dt

@app.get("/guests", response_model=list[schemas.GuestOut])
def list_guests(date: Optional[str] = Query(None), db=Depends(get_db)):
    # Determine date range for filtering
    qdate = dt.utcnow()
    if date:
        try:
            qdate = dt.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    start = dt.combine(qdate.date(), dt.min.time())
    end = dt.combine(qdate.date(), dt.max.time())

    # Exclude soft-deleted and filter by created_at date range
    guests = (
        db.query(models.Guest)
        .filter(models.Guest.deleted_at == None)
        .filter(models.Guest.created_at >= start, models.Guest.created_at <= end)
        .order_by(models.Guest.created_at.asc())
        .all()
    )
    return [schemas.GuestOut.model_validate(g, from_attributes=True) for g in guests]


@app.get("/guests/latest", response_model=schemas.GuestOut)
def latest_guest(date: Optional[str] = Query(None), db=Depends(get_db)):
    if date is None:
        date = dt.utcnow().strftime("%Y-%m-%d")
    start = dt.strptime(date, "%Y-%m-%d")
    end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
    latest = (
        db.query(models.Guest)
        .filter(models.Guest.deleted_at.is_(None))
        .filter(models.Guest.created_at >= start)
        .filter(models.Guest.created_at <= end)
        .order_by(models.Guest.created_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No guests for date")
    return schemas.GuestOut.model_validate(latest, from_attributes=True)


@app.get("/checkins/stream")
async def stream_checkins(date: Optional[str] = Query(None), db=Depends(get_db)):
    """Server-Sent Events stream of new check-ins for a date (default: today)."""
    if date is None:
        date = dt.utcnow().strftime("%Y-%m-%d")
    start = dt.strptime(date, "%Y-%m-%d")
    end = start.replace(hour=23, minute=59, second=59, microsecond=999999)

    async def event_generator():
        last_id = None
        while True:
            try:
                s = SessionLocal()
                try:
                    latest = (
                        s.query(models.Guest)
                        .filter(models.Guest.deleted_at.is_(None))
                        .filter(models.Guest.created_at >= start)
                        .filter(models.Guest.created_at <= end)
                        .order_by(models.Guest.created_at.desc())
                        .first()
                    )
                finally:
                    s.close()
                if latest and latest.id != last_id:
                    last_id = latest.id
                    payload_obj = schemas.GuestOut.model_validate(latest, from_attributes=True).model_dump()
                    hist = guest_history(latest.id, db)
                    payload_obj["history_count"] = len(hist)
                    try:
                        if latest.dnr_hit_id:
                            hit = db.get(models.Blacklist, latest.dnr_hit_id)
                            payload_obj["dnr_notes"] = hit.notes if hit else None
                    except Exception:
                        payload_obj["dnr_notes"] = None
                    payload = json.dumps(payload_obj)
                    yield f"data: {payload}\n\n"
            except Exception as e:
                yield f": error {str(e)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/guest/{guest_id}", response_model=schemas.GuestOut)
def get_guest(guest_id: int, db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    return schemas.GuestOut.model_validate(g, from_attributes=True)


@app.post("/guest/{guest_id}/update", response_model=schemas.GuestOut)
def update_guest(
    guest_id: int,
    first_name: Optional[str] = Form(None),
    middle_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    id_number: Optional[str] = Form(None),
    expiration_date: Optional[str] = Form(None),
    issue_date: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    zip_code: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    phone_country_code: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    room_number: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    override_dnr: bool = Form(False),
    admin_pin: Optional[str] = Form(None),
    dnr_clear: bool = Form(False),
    db=Depends(get_db),
    request: Request = None,
):
    g = db.query(models.Guest).get(guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")

    # Server-side DNR restriction: block edits while DNR is active unless clearing
    def _has_dnr(guest: models.Guest) -> bool:
        cur = str(guest.remarks or "")
        if "dnr" in cur.lower():
            return True
        if guest.dnr_hit_id:
            return True
        return bool(guest.dnr_hit_id)

    if _has_dnr(g) and not dnr_clear:
        raise HTTPException(status_code=403, detail="Guest is DNR; updates are restricted")

    if dnr_clear:
        # Require admin privileges or valid admin PIN
        ok = False
        try:
            ok = bool(admin_pin and verify_admin_pin(admin_pin))
        except Exception:
            ok = False
        if not ok:
            try:
                _ = get_current_admin(request)
                ok = True
            except Exception:
                pass
        if not ok:
            raise HTTPException(status_code=403, detail="Admin required to clear DNR")
        # Strip DNR from current record remarks
        cur = str(remarks if remarks is not None else g.remarks or "")
        def _strip_dnr(t: str) -> str:
            tt = t
            if "dnr" not in tt.lower():
                return tt
            tt = re.sub(r"^\s*dnr\s*—\s*", "", tt, flags=re.IGNORECASE)
            tt = re.sub(r"^\s*dnr\s*", "", tt, flags=re.IGNORECASE)
            return tt.strip()
        cur2 = _strip_dnr(cur)
        g.remarks = cur2
        g.dnr_hit_id = None
        g.dnr_match_score = None
        g.dnr_match_tier = None
        # Cascade: remove DNR tag from history entries
        try:
            ident = g.identity_hash or None
            q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
            if g.id_number:
                q = q.filter((models.Guest.id_number == g.id_number) | (models.Guest.identity_hash == ident))
            else:
                q = q.filter(models.Guest.identity_hash == ident)
            rows = q.all()
            for r in rows:
                curh = str(r.remarks or "")
                r.remarks = _strip_dnr(curh)
                r.dnr_hit_id = None
                r.dnr_match_score = None
        except Exception:
            pass
        try:
            actor = None
            try:
                actor = get_current_user(request).get("sub")
            except Exception:
                actor = "user"
            logging.info(json.dumps({
                "event": "dnr_status_change",
                "guest_id": g.id,
                "set": False,
                "actor": actor,
                "ts": datetime.utcnow().isoformat(),
            }))
        except Exception:
            pass

    if first_name is not None: g.first_name = first_name
    if middle_name is not None: g.middle_name = middle_name
    if last_name is not None: g.last_name = last_name
    if dob is not None: g.dob = iso_to_us_date(dob)
    if id_number is not None: g.id_number = id_number
    if expiration_date is not None: g.expiration_date = iso_to_us_date(expiration_date)
    if issue_date is not None: g.issue_date = iso_to_us_date(issue_date)
    validate_date_range(
        normalize_date_to_iso(g.dob),
        normalize_date_to_iso(g.issue_date),
        normalize_date_to_iso(g.expiration_date)
    )
    if address is not None: g.address = address
    if city is not None: g.city = city
    if state is not None: g.state = state
    if zip_code is not None: g.zip_code = zip_code
    if nationality is not None: g.nationality = nationality
    if phone_country_code is not None: g.phone_country_code = phone_country_code
    if phone_number is not None: g.phone_number = phone_number
    if room_number is not None: g.room_number = room_number
    if remarks is not None: g.remarks = remarks
    g.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        from .dnr_manager import dnr_match, _norm_name, _norm_dob, _norm_id, identity_hash
        g.first_name_norm = _norm_name(g.first_name)
        g.last_name_norm = _norm_name(g.last_name)
        g.dob_iso = _norm_dob(g.dob)
        g.id_number_norm = _norm_id(g.id_number)
        g.identity_hash = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
        if not dnr_clear:
            hit, score, tier = dnr_match(db, g)
            g.dnr_hit_id = hit.id if hit else None
            g.dnr_match_score = str(score) if score else None
            if hit:
                cur = str(g.remarks or "")
                if "dnr" not in cur.lower():
                    g.remarks = ("DNR — " + cur).strip()
    except Exception:
        pass
    db.commit()
    db.refresh(g)
    return schemas.GuestOut.model_validate(g, from_attributes=True)


@app.get("/image")
def get_image(path: str = Query(...), request: Request = None):
    rp = os.path.realpath(path)
    allowed = [
        os.path.realpath(filepaths.SCANS_DIR),
        os.path.realpath(filepaths.TEMP_DIR),
        os.path.realpath(filepaths.BACKUP_DIR),
    ]
    if not any(rp.startswith(a + os.sep) or rp == a for a in allowed):
        legacy = rp.replace("\\", "/")
        rebased = None
        try:
            if "/backend/temp/" in legacy:
                base = os.path.basename(rp)
                cand = os.path.join(filepaths.TEMP_DIR, base)
                if os.path.exists(cand):
                    rebased = os.path.realpath(cand)
            elif "/scans/" in legacy:
                rel = legacy.split("/scans/", 1)[1]
                cand = os.path.join(filepaths.SCANS_DIR, *rel.split("/"))
                if os.path.exists(cand):
                    rebased = os.path.realpath(cand)
            elif "/backup/" in legacy:
                rel = legacy.split("/backup/", 1)[1]
                cand = os.path.join(filepaths.BACKUP_DIR, *rel.split("/"))
                if os.path.exists(cand):
                    rebased = os.path.realpath(cand)
        except Exception:
            rebased = None
        if rebased:
            rp = rebased
        else:
            try:
                logging.warning(json.dumps({"event": "image_path_rejected", "path": rp, "ts": datetime.now(timezone.utc).isoformat()}))
            except Exception:
                pass
            raise HTTPException(status_code=403, detail="Unauthorized path")
    if not os.path.exists(rp):
        try:
            logging.warning(json.dumps({"event": "image_missing", "path": rp, "ts": datetime.now(timezone.utc).isoformat()}))
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Image not found")
    if not rp.lower().endswith(".jpg.enc"):
        try:
            logging.warning(json.dumps({"event": "image_invalid_ext", "path": rp, "ts": datetime.now(timezone.utc).isoformat()}))
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Invalid image path")
    enc = open(rp, "rb").read()
    try:
        dec = decrypt_bytes(enc)
    except Exception as e:
        try:
            logging.error(json.dumps({"event": "image_decrypt_error", "path": rp, "error": str(e), "ts": datetime.now(timezone.utc).isoformat()}))
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Image decrypt failed")
    return Response(content=dec, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=604800"})


@app.get("/")
def root():
    # Friendly landing response for the API root
    return JSONResponse({
        "status": "ok",
        "service": "IDscnr API",
        "message": "Visit /docs for interactive API docs.",
        "links": {
            "docs": "/docs",
            "health": "/health",
            "ocr_health": "/ocr/health",
        }
    })


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


# Centralized exception handling to provide user-friendly errors and structured logs
from fastapi import Request
from .security import decrypt_str
import logging


@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    logging.error(json.dumps({
        "event": "exception",
        "path": request.url.path,
        "error": str(exc),
        "ts": datetime.now(timezone.utc).isoformat(),
    }))
    # Provide friendly messages for common situations
    msg = str(exc)
    if "Duplicate" in msg or "409" in msg:
        detail = "Duplicate or DNR conflict detected."
    elif "Scanner" in msg:
        detail = "Scanner error. Please check device and try Upload mode."
    elif "OCR" in msg:
        detail = "OCR error or timeout. Try again or switch provider."
    else:
        detail = "Unexpected error occurred."
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/logs")
def get_logs(lines: int = 200, request: Request = None):
    log_path = os.path.join(os.path.dirname(__file__), 'data', 'app.log')
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read().splitlines()
        return {"lines": content[-max(1, lines):]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot read logs: {e}")


@app.get("/ocr/health")
def ocr_health():
    """Lightweight endpoint to test Tesseract OCR functionality.
    Returns JSON with ok status and optional reason/text.
    """
    try:
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a basic font, fallback to default if not available
        try:
            font = ImageFont.load_default()
            draw.text((10, 10), "TEST OCR", fill='black', font=font)
        except:
            draw.text((10, 10), "TEST OCR", fill='black')
        
        # Save to temporary file and test OCR
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        try:
            img.save(tmp.name)
        finally:
            try:
                tmp.close()
            except Exception:
                pass
        prov = _settings.get("ocr_provider")
        if prov == "google" and _settings.get("google_api_key"):
            try:
                from .ocr_utils import extract_text_google
                result = extract_text_google(tmp.name, _settings.get("google_api_key"))
                os.unlink(tmp.name)
                if result and ("TEST" in result.upper() or "OCR" in result.upper()):
                    return JSONResponse({"ok": True, "text": result.strip(), "provider": "google"})
                else:
                    return JSONResponse({"ok": True, "text": result.strip() if result else "", "provider": "google", "note": "Test text not detected"})
            except Exception as e:
                try:
                    os.unlink(tmp.name)
                except:
                    pass
                logging.error(f"OCR health check failed: {e}")
                return JSONResponse({"ok": False, "reason": f"google_error: {str(e)}", "provider": "google"})
        else:
            try:
                from .ocr_utils import extract_text_tesseract
                result = extract_text_tesseract(tmp.name)
                os.unlink(tmp.name)
                if result and ("TEST" in result.upper() or "OCR" in result.upper()):
                    return JSONResponse({"ok": True, "text": result.strip(), "provider": "tesseract"})
                else:
                    return JSONResponse({"ok": True, "text": result.strip() if result else "", "provider": "tesseract", "note": "Test text not detected but OCR is working"})
            except Exception as e:
                try:
                    os.unlink(tmp.name)
                except:
                    pass
                logging.error(f"OCR health check failed: {e}")
                return JSONResponse({"ok": False, "reason": f"tesseract_error: {str(e)}", "provider": "tesseract"})
    except Exception as e:
        logging.error(f"OCR health check setup failed: {e}")
        return JSONResponse({"ok": False, "reason": f"setup_error: {str(e)}", "provider": "tesseract"})


## Removed legacy /scan/device/preview endpoint


# Enumerate scanner devices
@app.get("/scan/devices")
def scan_devices():
    try:
        return {"devices": list_scan_devices()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device enumeration failed: {e}")


# --- Auth ---
from fastapi import Request


@app.post("/auth/login")
def auth_login(request: Request, username: Optional[str] = Form(None), password: Optional[str] = Form(None), pin: Optional[str] = Form(None), pin_enc: Optional[str] = Form(None)):
    # Login via admin PIN or username/password stored in config/users.json
    import hashlib
    secret = _jwt_secret_env or _settings.get("jwt_secret") or "dev-secret-change-me"
    role = None
    subject = None
    # Basic rate limiting per IP
    ip = request.client.host if request and request.client else "unknown"
    now = time.time()
    window = 300
    max_attempts = 20
    _rl = getattr(auth_login, "_rl", {})
    # prune
    auth_login._rl = {k: [t for t in v if now - t < window] for k, v in _rl.items()}
    attempts = auth_login._rl.get(ip, [])
    if len(attempts) >= max_attempts:
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait.")
    attempts.append(now)
    auth_login._rl[ip] = attempts

    # Support encrypted PIN
    if pin_enc and not pin:
        try:
            pin = decrypt_str(pin_enc)
        except Exception:
            pin = None
    if pin:
        if not verify_pin(pin):
            raise HTTPException(status_code=401, detail="Invalid PIN")
        role = "admin"
        subject = "admin_pin"
    elif username and password:
        users_path = os.path.join(os.path.dirname(__file__), "config", "users.json")
        try:
            users = json.load(open(users_path, "r"))
        except Exception:
            users = {}
        entry = users.get(username)
        if not entry:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        h = hashlib.sha256(password.encode("utf-8")).digest()
        if base64.b64encode(h).decode() != entry.get("password_hash"):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        role = entry.get("role") or "staff"
        subject = username
    else:
        raise HTTPException(status_code=400, detail="Provide PIN or username/password")

    exp = int(time.time()) + 1800
    token = create_jwt({"sub": subject, "role": role, "exp": exp}, secret)
    return {"access_token": token, "token_type": "bearer", "role": role}


def get_current_user(request: Request) -> dict:
    token = get_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    secret = _jwt_secret_env or _settings.get("jwt_secret") or "dev-secret-change-me"
    payload = verify_jwt(token, secret)
    return payload


def get_current_admin(request: Request) -> dict:
    user = get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user


# Settings endpoints
@app.get("/settings/get")
def settings_get():
    return _settings


@app.post("/settings/update")
def settings_update(
    ocr_provider: Optional[str] = Form(None),
    scan_device: Optional[str] = Form(None),
    auto_pms_write: Optional[bool] = Form(None),
    cors_origins: Optional[str] = Form(None),  # comma-separated
    dark_mode: Optional[bool] = Form(None),
    pms_export_mode: Optional[str] = Form(None),
    pms_export_path: Optional[str] = Form(None),
    pms_api_url: Optional[str] = Form(None),
    pms_window_title: Optional[str] = Form(None),
    pms_autofill_tab_order: Optional[str] = Form(None),
    pms_autofill_delay_ms: Optional[str] = Form(None),
    google_api_key: Optional[str] = Form(None),
    request: Request = None,
):
    # Require admin authentication
    try:
        get_current_admin(request)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin required")
    if ocr_provider in {"tesseract", "google"}:
        _settings["ocr_provider"] = ocr_provider
    if google_api_key is not None:
        _settings["google_api_key"] = google_api_key
    if scan_device is not None:
        _settings["scan_device"] = scan_device
    if auto_pms_write is not None:
        _settings["auto_pms_write"] = bool(auto_pms_write)
    if cors_origins is not None:
        _settings["cors_origins"] = [o.strip() for o in cors_origins.split(",") if o.strip()]
    if dark_mode is not None:
        _settings["dark_mode"] = bool(dark_mode)
    if pms_export_mode in {"json", "csv", "api"}:
        _settings["pms_export_mode"] = pms_export_mode
    if pms_export_path is not None:
        _settings["pms_export_path"] = pms_export_path
    if pms_api_url is not None:
        _settings["pms_api_url"] = pms_api_url
    if pms_window_title is not None:
        _settings["pms_window_title"] = pms_window_title
    if pms_autofill_tab_order is not None:
        _settings["pms_autofill_tab_order"] = [o.strip() for o in pms_autofill_tab_order.split(",") if o.strip()]
    if pms_autofill_delay_ms is not None:
        try:
            _settings["pms_autofill_delay_ms"] = int(pms_autofill_delay_ms)
        except Exception:
            pass
    save_settings(_settings)
    return {"status": "ok", "settings": _settings}


@app.post("/admin/pin/update")
def admin_pin_update(current_pin: str = Form(...), new_pin: str = Form(...), request: Request = None):
    # Require admin authentication
    try:
        get_current_admin(request)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin required")
    if not verify_pin(current_pin):
        raise HTTPException(status_code=403, detail="Invalid current PIN")
    update_pin(new_pin)
    return {"status": "ok"}


@app.post("/pms/write")
def pms_write(guest_id: int, override_dnr: bool = False, admin_pin: Optional[str] = None, override_reason: Optional[str] = None, db=Depends(get_db), request: Request = None):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    from .dnr_manager import dnr_match
    hit, score, tier = dnr_match(db, g)
    if hit:
        g.dnr_hit_id = hit.id
        g.dnr_match_score = str(score)
        if not override_dnr:
            db.commit()
            raise HTTPException(status_code=409, detail="DNR match detected")
        if override_dnr:
            actor = None
            try:
                actor = get_current_user(request).get("sub")
            except Exception:
                actor = "user"
            g.dnr_override_by = actor
            g.dnr_override_reason = override_reason or "override"
            g.dnr_override_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            try:
                logging.info(json.dumps({
                    "event": "dnr_override",
                    "guest_id": g.id,
                    "dnr_hit_id": hit.id,
                    "score": score,
                    "actor": actor,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }))
            except Exception:
                pass
    path = write_guest_to_pms(g)
    return {"status": "ok", "export_path": path}


@app.post("/pms/autofill")
def pms_autofill(guest_id: int, db=Depends(get_db)):
    if os.name != "nt":
        raise HTTPException(status_code=501, detail="Windows only")
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    try:
        from .pms_autofill import _find_window, autofill_guest
        hwnd = _find_window(_settings.get("pms_window_title"))
        if not hwnd:
            raise HTTPException(status_code=404, detail="PMS window not found")
        tab_order = _settings.get("pms_autofill_tab_order") or []
        delay_ms = int(_settings.get("pms_autofill_delay_ms") or 50)
        result = autofill_guest(hwnd, g, tab_order, delay_ms)
        return {"status": "ok", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/guest/{guest_id}/upload-image")
async def upload_image(guest_id: int, side: str = Form(...), file: UploadFile = File(...), db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    if side not in {"front", "back"}:
        raise HTTPException(status_code=400, detail="Invalid side")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large")
    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        data = buf.getvalue()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")
    enc = encrypt_bytes(data)
    path = filepaths.get_temp_encrypted_image_path(side)
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(enc)
    if side == "front":
        g.image_front_path = path
    else:
        g.image_back_path = path
    db.commit()
    db.refresh(g)
    return {"status": "ok", "path": path}


@app.post("/guest/{guest_id}/process-images")
def process_guest_images(guest_id: int, overwrite: bool = True, db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    front_plain = None
    back_plain = None
    try:
        if g.image_front_path and os.path.exists(g.image_front_path):
            enc = open(g.image_front_path, "rb").read()
            front_plain = filepaths.get_temp_image_path("front")
            with open(front_plain, "wb") as f:
                f.write(decrypt_bytes(enc))
        if g.image_back_path and os.path.exists(g.image_back_path):
            enc2 = open(g.image_back_path, "rb").read()
            back_plain = filepaths.get_temp_image_path("back")
            with open(back_plain, "wb") as f:
                f.write(decrypt_bytes(enc2))
        sd = extract_structured_data(front_plain, back_plain)
        try:
            from .ocr_utils import extract_structured_data_with_provider
            prov = _settings.get("ocr_provider")
            api_key = _settings.get("google_api_key")
            sd = extract_structured_data_with_provider(front_plain, back_plain, prov, api_key)
        except Exception:
            sd = extract_structured_data(front_plain, back_plain)
        try:
            logging.info(json.dumps({
                "event": "ocr_result",
                "guest_id": g.id,
                "dob_raw": sd.date_of_birth,
                "issue_raw": sd.issue_date,
                "exp_raw": sd.expiration_date,
                "ts": datetime.now(timezone.utc).isoformat(),
            }))
        except Exception:
            pass
        if overwrite:
            g.first_name = sd.first_name or g.first_name
            g.last_name = sd.last_name or g.last_name
            ndob = iso_to_us_date(sd.date_of_birth) or g.dob
            niss = iso_to_us_date(sd.issue_date) or g.issue_date
            nexp = iso_to_us_date(sd.expiration_date) or g.expiration_date
            try:
                validate_date_range(
                    normalize_date_to_iso(ndob),
                    normalize_date_to_iso(niss),
                    normalize_date_to_iso(nexp)
                )
                g.dob = ndob
                g.issue_date = niss
                g.expiration_date = nexp
            except HTTPException:
                g.remarks = ("VERIFY DOB — " + (g.remarks or "")).strip()
            g.address = sd.address or g.address
            g.city = sd.city or g.city
            g.state = sd.state or g.state
            g.zip_code = sd.zip_code or g.zip_code
            g.nationality = sd.nationality or g.nationality
            g.raw_text = sd.raw_text or g.raw_text
        from .dnr_manager import dnr_match, _norm_name, _norm_dob, _norm_id, identity_hash
        try:
            nid = _norm_id(g.id_number)
            ident = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
            if not (g.first_name and g.last_name and g.dob and g.id_number):
                q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
                if nid:
                    q = q.filter(models.Guest.id_number_norm == nid)
                else:
                    q = q.filter(models.Guest.identity_hash == ident)
                prior = q.filter(models.Guest.id != g.id).order_by(models.Guest.created_at.desc()).first()
                if prior:
                    g.first_name = g.first_name or prior.first_name
                    g.last_name = g.last_name or prior.last_name
                    g.dob = g.dob or prior.dob
                    g.id_number = g.id_number or prior.id_number
                    g.issue_date = g.issue_date or prior.issue_date
                    g.expiration_date = g.expiration_date or prior.expiration_date
                    g.address = g.address or prior.address
                    g.city = g.city or prior.city
                    g.state = g.state or prior.state
                    g.zip_code = g.zip_code or prior.zip_code
                    g.nationality = g.nationality or prior.nationality
        except Exception:
            pass
        g.first_name_norm = _norm_name(g.first_name)
        g.last_name_norm = _norm_name(g.last_name)
        g.dob_iso = _norm_dob(g.dob)
        g.id_number_norm = _norm_id(g.id_number)
        g.identity_hash = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
        hit, score, tier = dnr_match(db, g)
        g.dnr_hit_id = hit.id if hit else None
        g.dnr_match_score = str(score) if score else None
        if hit:
            cur = str(g.remarks or "")
            if "dnr" not in cur.lower():
                g.remarks = ("DNR — " + cur).strip()
        g.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(g)
        return schemas.GuestOut.model_validate(g, from_attributes=True)
    finally:
        for p in [front_plain, back_plain]:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass


@app.get("/guest/{guest_id}/audit-dates")
def guest_audit_dates(guest_id: int, db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    front_plain = None
    back_plain = None
    try:
        if g.image_front_path and os.path.exists(g.image_front_path):
            enc = open(g.image_front_path, "rb").read()
            dec = decrypt_bytes(enc)
            front_plain = filepaths.get_temp_image_path("front")
            open(front_plain, "wb").write(dec)
        if g.image_back_path and os.path.exists(g.image_back_path):
            enc2 = open(g.image_back_path, "rb").read()
            dec2 = decrypt_bytes(enc2)
            back_plain = filepaths.get_temp_image_path("back")
            open(back_plain, "wb").write(dec2)
        sd = extract_structured_data(front_plain, back_plain)
        dob_iso = normalize_date_to_iso(sd.date_of_birth)
        issue_iso = normalize_date_to_iso(sd.issue_date)
        exp_iso = normalize_date_to_iso(sd.expiration_date)
        try:
            from .ocr_utils import extract_structured_data_with_provider
            prov = _settings.get("ocr_provider")
            api_key = _settings.get("google_api_key")
            sd = extract_structured_data_with_provider(front_plain, back_plain, prov, api_key)
            dob_iso = normalize_date_to_iso(sd.date_of_birth)
            issue_iso = normalize_date_to_iso(sd.issue_date)
            exp_iso = normalize_date_to_iso(sd.expiration_date)
        except Exception:
            pass
        def age(iso):
            dt = parse_iso_date(iso)
            if not dt:
                return None
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            return int((now - dt).days // 365)
        return {
            "current": {"dob": g.dob, "issue": g.issue_date, "exp": g.expiration_date},
            "parsed": {"dob": sd.date_of_birth, "issue": sd.issue_date, "exp": sd.expiration_date},
            "normalized_iso": {"dob": dob_iso, "issue": issue_iso, "exp": exp_iso},
            "ages": {"dob": age(dob_iso)},
            "raw_text_present": bool(g.raw_text),
        }
    finally:
        for p in [front_plain, back_plain]:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass


@app.get("/guest/{guest_id}/ocr-debug")
def guest_ocr_debug(guest_id: int, db=Depends(get_db)):
    """Debug endpoint to see raw OCR text and parsed results."""
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    front_plain = None
    back_plain = None
    try:
        if g.image_front_path and os.path.exists(g.image_front_path):
            enc = open(g.image_front_path, "rb").read()
            dec = decrypt_bytes(enc)
            front_plain = filepaths.get_temp_image_path("front")
            open(front_plain, "wb").write(dec)
        if g.image_back_path and os.path.exists(g.image_back_path):
            enc2 = open(g.image_back_path, "rb").read()
            dec2 = decrypt_bytes(enc2)
            back_plain = filepaths.get_temp_image_path("back")
            open(back_plain, "wb").write(dec2)
        
        from .ocr_utils import extract_text_tesseract, parse_fields_from_text, parse_aamva_from_barcode
        
        front_text = extract_text_tesseract(front_plain) if front_plain else ""
        back_text = extract_text_tesseract(back_plain) if back_plain else ""
        front_barcode = parse_aamva_from_barcode(front_plain) if front_plain else {}
        back_barcode = parse_aamva_from_barcode(back_plain) if back_plain else {}
        
        front_parsed = parse_fields_from_text(front_text) if front_text else {}
        back_parsed = parse_fields_from_text(back_text) if back_text else {}
        
        try:
            from .ocr_utils import extract_structured_data_with_provider
            prov = _settings.get("ocr_provider")
            api_key = _settings.get("google_api_key")
            sd = extract_structured_data_with_provider(front_plain, back_plain, prov, api_key)
        except Exception:
            sd = extract_structured_data(front_plain, back_plain)
        
        return {
            "front_raw_text": front_text,
            "back_raw_text": back_text,
            "front_barcode": front_barcode,
            "back_barcode": back_barcode,
            "front_parsed": front_parsed,
            "back_parsed": back_parsed,
            "final_structured_data": {
                "first_name": sd.first_name,
                "last_name": sd.last_name,
                "middle_name": sd.middle_name,
                "date_of_birth": sd.date_of_birth,
                "id_number": sd.id_number,
                "expiration_date": sd.expiration_date,
                "issue_date": sd.issue_date,
                "address": sd.address,
                "city": sd.city,
                "state": sd.state,
                "zip_code": sd.zip_code,
            },
            "current_guest_data": {
                "first_name": g.first_name,
                "last_name": g.last_name,
                "dob": g.dob,
                "id_number": g.id_number,
            }
        }
    finally:
        for p in [front_plain, back_plain]:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass


# --- Auto-scan folder utilities ---
@app.get("/scan-files/today")
def scan_files_today():
    """List encrypted scan files saved today with basic metadata."""
    d = filepaths.get_today_scan_dir()
    if not os.path.exists(d):
        return []
    items = []
    for name in os.listdir(d):
        if not name.endswith(".jpg.enc"):
            continue
        fp = os.path.join(d, name)
        mtime = datetime.utcfromtimestamp(os.path.getmtime(fp)).isoformat()
        side = "front" if "_front" in name else ("back" if "_back" in name else "unknown")
        guest_slug = name.replace("_front.jpg.enc", "").replace("_back.jpg.enc", "")
        items.append({
            "file_path": fp,
            "guest_slug": guest_slug,
            "side": side,
            "modified_at": mtime,
        })
    return items


## Removed legacy /scan/process-file endpoint


# --- DNR Admin Endpoints ---
@app.get("/dnr")
def list_dnr(q: Optional[str] = Query(None), db=Depends(get_db)):
    entries_q = db.query(models.Blacklist)
    if q:
        qs = q.strip().lower()
        entries_q = entries_q.filter(
            (models.Blacklist.first_name_norm.ilike(f"%{qs}%")) |
            (models.Blacklist.last_name_norm.ilike(f"%{qs}%")) |
            (models.Blacklist.id_number_norm.ilike(f"%{qs.upper()}%"))
        )
    entries = entries_q.order_by(models.Blacklist.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "dob": e.dob,
            "id_number": e.id_number,
            "notes": e.notes,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in entries
    ]


@app.post("/dnr")
def add_dnr(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    id_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db=Depends(get_db),
    request: Request = None,
):
    
    from .dnr_manager import _norm_name, _norm_dob, _norm_id
    entry = models.Blacklist(
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        id_number=id_number,
        notes=notes,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        first_name_norm=_norm_name(first_name),
        last_name_norm=_norm_name(last_name),
        dob_iso=_norm_dob(dob),
        id_number_norm=_norm_id(id_number),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    try:
        from .dnr_manager import identity_hash
        ident = identity_hash(first_name, last_name, dob, id_number)
        q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
        if entry.id_number_norm:
            q = q.filter((models.Guest.id_number_norm == entry.id_number_norm) | (models.Guest.identity_hash == ident))
        else:
            q = q.filter(models.Guest.identity_hash == ident)
        rows = q.all()
        for r in rows:
            r.dnr_hit_id = entry.id
            cur = str(r.remarks or "")
            if "dnr" not in cur.lower():
                r.remarks = ("DNR — " + cur).strip()
        db.commit()
    except Exception:
        pass
    try:
        logging.info(json.dumps({
            "event": "dnr_add",
            "id": entry.id,
            "first_name": entry.first_name,
            "last_name": entry.last_name,
            "dob": entry.dob,
            "id_number": entry.id_number,
            "ts": datetime.now(timezone.utc).isoformat(),
        }))
    except Exception:
        pass
    return {"status": "ok", "id": entry.id}


@app.delete("/dnr/{entry_id}")
def delete_dnr(entry_id: int, db=Depends(get_db), request: Request = None):
    e = db.get(models.Blacklist, entry_id)
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    # Cascade removal: clear DNR fields and strip remarks on all guests linked to this entry
    try:
        def _strip_dnr(t: str) -> str:
            tt = t or ""
            if "dnr" not in tt.lower():
                return tt
            tt = re.sub(r"^\s*dnr\s*—\s*", "", tt, flags=re.IGNORECASE)
            tt = re.sub(r"^\s*dnr\s*", "", tt, flags=re.IGNORECASE)
            return tt.strip()
        # Guests directly linked via hit id
        rows = db.query(models.Guest).filter(models.Guest.dnr_hit_id == entry_id).all()
        for r in rows:
            r.remarks = _strip_dnr(str(r.remarks or ""))
            r.dnr_hit_id = None
            r.dnr_match_score = None
            r.dnr_match_tier = None
        db.commit()
    except Exception:
        pass
    # Delete blacklist entry after cascade
    db.delete(e)
    db.commit()
    try:
        logging.info(json.dumps({
            "event": "dnr_delete",
            "id": entry_id,
            "ts": datetime.utcnow().isoformat(),
        }))
    except Exception:
        pass
    return {"status": "ok"}


@app.post("/guest/{guest_id}/dnr")
def set_guest_dnr(
    guest_id: int,
    set: bool = Form(...),
    admin_pin: Optional[str] = Form(None),
    admin_pin_enc: Optional[str] = Form(None),
    db=Depends(get_db),
    request: Request = None,
):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")

    def _strip_dnr(t: str) -> str:
        tt = t or ""
        if "dnr" not in tt.lower():
            return tt
        tt = re.sub(r"^\s*dnr\s*—\s*", "", tt, flags=re.IGNORECASE)
        tt = re.sub(r"^\s*dnr\s*", "", tt, flags=re.IGNORECASE)
        return tt.strip()

    if admin_pin_enc and not admin_pin:
        try:
            admin_pin = decrypt_str(admin_pin_enc)
        except Exception:
            admin_pin = None
    if not set:
        ok = False
        try:
            ok = bool(admin_pin and verify_admin_pin(admin_pin))
        except Exception:
            ok = False
        if not ok:
            try:
                _ = get_current_admin(request)
                ok = True
            except Exception:
                pass
        if not ok:
            raise HTTPException(status_code=403, detail="Admin required to remove DNR")

    if set:
        cur = str(g.remarks or "")
        if "dnr" not in cur.lower():
            g.remarks = ("DNR — " + cur).strip()
        try:
            from .dnr_manager import _norm_name, _norm_dob, _norm_id, identity_hash
            fn = _norm_name(g.first_name)
            ln = _norm_name(g.last_name)
            dob_iso = _norm_dob(g.dob)
            id_norm = _norm_id(g.id_number)
            e = None
            if id_norm:
                e = db.query(models.Blacklist).filter(models.Blacklist.id_number_norm == id_norm).first()
            if not e:
                e = models.Blacklist(first_name=fn, last_name=ln, dob=dob_iso, id_number=g.id_number, first_name_norm=fn, last_name_norm=ln, dob_iso=dob_iso, id_number_norm=id_norm, created_at=datetime.utcnow())
                db.add(e)
                db.commit(); db.refresh(e)
            ident = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
            q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
            if g.id_number:
                q = q.filter((models.Guest.id_number == g.id_number) | (models.Guest.identity_hash == ident))
            else:
                q = q.filter(models.Guest.identity_hash == ident)
            rows = q.all()
            for r in rows:
                r.dnr_hit_id = e.id
                curh = str(r.remarks or "")
                if "dnr" not in curh.lower():
                    r.remarks = ("DNR — " + curh).strip()
            db.commit()
        except Exception:
            db.commit()
    else:
        try:
            from .dnr_manager import _norm_name, _norm_dob, _norm_id, identity_hash
            fn = _norm_name(g.first_name)
            ln = _norm_name(g.last_name)
            dob_iso = _norm_dob(g.dob)
            id_norm = _norm_id(g.id_number)
            qbl = db.query(models.Blacklist)
            targets = []
            if id_norm:
                targets = qbl.filter(models.Blacklist.id_number_norm == id_norm).all()
            else:
                targets = qbl.filter(
                    (models.Blacklist.first_name_norm == fn) &
                    (models.Blacklist.last_name_norm == ln) &
                    (models.Blacklist.dob_iso == dob_iso)
                ).all()
            if g.dnr_hit_id:
                try:
                    e2 = db.get(models.Blacklist, g.dnr_hit_id)
                    if e2 and all(e.id != e2.id for e in targets):
                        targets.append(e2)
                except Exception:
                    pass
            target_ids = [e.id for e in targets]
            for e in targets:
                db.delete(e)
            ident = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
            q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
            if g.id_number:
                cond = (models.Guest.id_number == g.id_number) | (models.Guest.identity_hash == ident)
            else:
                cond = (models.Guest.identity_hash == ident)
            if target_ids:
                cond = cond | (models.Guest.dnr_hit_id.in_(target_ids))
            q = q.filter(cond)
            rows = q.all()
            for r in rows:
                r.remarks = _strip_dnr(str(r.remarks or ""))
                r.dnr_hit_id = None
                r.dnr_match_score = None
                r.dnr_match_tier = None
            db.commit()
        except Exception:
            db.commit()

    try:
        actor = None
        try:
            actor = get_current_user(request).get("sub")
        except Exception:
            actor = "user"
        logging.info(json.dumps({
            "event": "dnr_status_change",
            "guest_id": g.id,
            "set": set,
            "actor": actor,
            "ts": datetime.utcnow().isoformat(),
        }))
    except Exception:
        pass
    return {"status": "ok"}


@app.get("/dnr/match")
def dnr_match_preview(guest_id: int, db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    from .dnr_manager import dnr_match
    hit, score, tier = dnr_match(db, g)
    return {
        "hit": ({
            "id": hit.id,
            "first_name": hit.first_name,
            "last_name": hit.last_name,
            "dob": hit.dob,
            "id_number": hit.id_number,
        } if hit else None),
        "score": score,
        "tier": tier,
    }


@app.get("/stats/mtd")
def stats_mtd(date: Optional[str] = Query(None), db=Depends(get_db)):
    base = dt.utcnow() if date is None else dt.strptime(date, "%Y-%m-%d")
    start = dt.strptime(base.strftime("%Y-%m-01"), "%Y-%m-%d")
    end = start.replace(month=start.month % 12 + 1, day=1) if start.month < 12 else start.replace(year=start.year + 1, month=1, day=1)
    count = (
        db.query(models.Guest)
        .filter(models.Guest.deleted_at.is_(None))
        .filter(models.Guest.created_at >= start)
        .filter(models.Guest.created_at < end)
    ).count()
    return {"mtd": count}


@app.get("/stats/daily")
def stats_daily(month: Optional[str] = Query(None), db=Depends(get_db)):
    base = dt.utcnow() if month is None else dt.strptime(month + "-01", "%Y-%m-%d")
    start = base.replace(day=1)
    end = start.replace(month=start.month % 12 + 1, day=1) if start.month < 12 else start.replace(year=start.year + 1, month=1, day=1)
    rows = (
        db.query(models.Guest.created_at)
        .filter(models.Guest.deleted_at.is_(None))
        .filter(models.Guest.created_at >= start)
        .filter(models.Guest.created_at < end)
        .all()
    )
    counts = {}
    for (created_at,) in rows:
        d = created_at.strftime("%Y-%m-%d") if created_at else None
        if d:
            counts[d] = counts.get(d, 0) + 1
    series = sorted([{ "date": d, "count": c } for d, c in counts.items()], key=lambda x: x["date"])
    return {"series": series}


@app.get("/stats/dnr")
def stats_dnr(month: Optional[str] = Query(None), db=Depends(get_db)):
    base = dt.utcnow() if month is None else dt.strptime(month + "-01", "%Y-%m-%d")
    start = base.replace(day=1)
    end = start.replace(month=start.month % 12 + 1, day=1) if start.month < 12 else start.replace(year=start.year + 1, month=1, day=1)
    rows = (
        db.query(models.Guest.dnr_hit_id, models.Guest.dnr_override_at, models.Guest.created_at)
        .filter(models.Guest.created_at >= start)
        .filter(models.Guest.created_at < end)
        .all()
    )
    total_hits = sum(1 for h, o, c in rows if h is not None)
    strong_hits = total_hits
    overrides = sum(1 for h, o, c in rows if o is not None)
    by_day = {}
    for h, o, c in rows:
        d = c.strftime("%Y-%m-%d") if c else None
        if not d:
            continue
        cur = by_day.get(d) or {"hits": 0, "strong": 0, "overrides": 0}
        if h is not None:
            cur["hits"] += 1
            cur["strong"] += 1
        if o is not None:
            cur["overrides"] += 1
        by_day[d] = cur
    series = sorted([{ "date": d, **m } for d, m in by_day.items()], key=lambda x: x["date"])
    return {"total_hits": total_hits, "strong_hits": strong_hits, "overrides": overrides, "series": series}


@app.get("/admin/overrides")
def admin_overrides(limit: int = 50, db=Depends(get_db), request: Request = None):
    
    rows = (
        db.query(models.Guest)
        .filter(models.Guest.dnr_override_at.isnot(None))
        .order_by(models.Guest.dnr_override_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return [
        {
            "guest_id": r.id,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "dnr_hit_id": r.dnr_hit_id,
            "reason": r.dnr_override_reason,
            "actor": r.dnr_override_by,
            "at": r.dnr_override_at.isoformat() if r.dnr_override_at else None,
        } for r in rows
    ]


@app.get("/guest/{guest_id}/history")
def guest_history(guest_id: int, db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    ident = g.identity_hash or None
    q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
    if g.id_number:
        q = q.filter((models.Guest.id_number == g.id_number) | (models.Guest.identity_hash == ident))
    else:
        q = q.filter(models.Guest.identity_hash == ident)
    items = (
        q.order_by(models.Guest.created_at.asc()).all()
    )
    return [
        {
            "id": x.id,
            "created_at": x.created_at.isoformat() if x.created_at else None,
            "room_number": x.room_number,
            "remarks": x.remarks,
            "image_front_path": x.image_front_path,
            "image_back_path": x.image_back_path,
        } for x in items
    ]


@app.get("/guest/{guest_id}/summary")
def guest_summary(guest_id: int, db=Depends(get_db)):
    g = db.get(models.Guest, guest_id)
    if not g:
        raise HTTPException(status_code=404, detail="Guest not found")
    h = guest_history(guest_id, db)
    count = len(h)
    last = h[-3:]
    return {
        "total_checkins": count,
        "recent": last,
    }
@app.post("/guest/sample")
def guest_sample(first_name: Optional[str] = Form("Jenice"), last_name: Optional[str] = Form("Test"), db=Depends(get_db)):
    g = models.Guest(
        first_name=first_name,
        last_name=last_name,
        dob="06/12/1994",
        id_number="SAMPLE1234",
        expiration_date="06/12/2030",
        issue_date="06/12/2024",
        address="123 Sample St",
        city="Sample City",
        state="CA",
        zip_code="90001",
        nationality="USA",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    from .dnr_manager import _norm_name, _norm_dob, _norm_id, identity_hash
    g.first_name_norm = _norm_name(g.first_name)
    g.last_name_norm = _norm_name(g.last_name)
    g.dob_iso = _norm_dob(g.dob)
    g.id_number_norm = _norm_id(g.id_number)
    g.identity_hash = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
    db.commit()
    db.refresh(g)
    return schemas.GuestOut.model_validate(g, from_attributes=True)
@app.post("/scan/ingest")
async def scan_ingest(front: UploadFile = File(...), back: UploadFile = File(None), db=Depends(get_db)):
    front_bytes = await front.read()
    back_bytes = await back.read() if back else None
    try:
        imgf = Image.open(io.BytesIO(front_bytes)).convert('RGB')
        bf = io.BytesIO(); imgf.save(bf, format='JPEG', quality=85); front_bytes = bf.getvalue()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid front image")
    if back_bytes:
        try:
            imgb = Image.open(io.BytesIO(back_bytes)).convert('RGB')
            bb = io.BytesIO(); imgb.save(bb, format='JPEG', quality=85); back_bytes = bb.getvalue()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid back image")
    fp_front_plain = filepaths.get_temp_image_path("front")
    fp_front_enc = filepaths.get_temp_encrypted_image_path("front")
    with open(fp_front_plain, "wb") as f:
        f.write(front_bytes)
    with open(fp_front_enc, "wb") as f:
        f.write(encrypt_bytes(front_bytes))
    fp_back_plain = None
    fp_back_enc = None
    if back_bytes:
        fp_back_plain = filepaths.get_temp_image_path("back")
        fp_back_enc = filepaths.get_temp_encrypted_image_path("back")
        with open(fp_back_plain, "wb") as f:
            f.write(back_bytes)
        with open(fp_back_enc, "wb") as f:
            f.write(encrypt_bytes(back_bytes))
    sd = extract_structured_data(fp_front_plain, fp_back_plain)
    try:
        from .ocr_utils import extract_structured_data_with_provider
        prov = _settings.get("ocr_provider")
        api_key = _settings.get("google_api_key")
        sd = extract_structured_data_with_provider(fp_front_plain, fp_back_plain, prov, api_key)
    except Exception:
        pass
    try:
        os.remove(fp_front_plain)
    except Exception:
        pass
    if fp_back_plain:
        try:
            os.remove(fp_back_plain)
        except Exception:
            pass
    g = models.Guest(
        first_name=sd.first_name,
        middle_name=sd.middle_name,
        last_name=sd.last_name,
        dob=iso_to_us_date(sd.date_of_birth),
        id_number=sd.id_number,
        expiration_date=iso_to_us_date(sd.expiration_date),
        issue_date=iso_to_us_date(sd.issue_date),
        address=sd.address,
        city=sd.city,
        state=sd.state,
        zip_code=sd.zip_code,
        nationality=sd.nationality,
        image_front_path=fp_front_enc,
        image_back_path=fp_back_enc,
        raw_text=sd.raw_text,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    try:
        from .dnr_manager import dnr_match, _norm_name, _norm_dob, _norm_id, identity_hash
        try:
            nid = _norm_id(g.id_number)
            ident = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
            if not (g.first_name and g.last_name and g.dob and g.id_number):
                q = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None))
                if nid:
                    q = q.filter(models.Guest.id_number_norm == nid)
                else:
                    q = q.filter(models.Guest.identity_hash == ident)
                prior = q.filter(models.Guest.id != g.id).order_by(models.Guest.created_at.desc()).first()
                if prior:
                    g.first_name = g.first_name or prior.first_name
                    g.last_name = g.last_name or prior.last_name
                    g.dob = g.dob or prior.dob
                    g.id_number = g.id_number or prior.id_number
                    g.issue_date = g.issue_date or prior.issue_date
                    g.expiration_date = g.expiration_date or prior.expiration_date
                    g.address = g.address or prior.address
                    g.city = g.city or prior.city
                    g.state = g.state or prior.state
                    g.zip_code = g.zip_code or prior.zip_code
                    g.nationality = g.nationality or prior.nationality
        except Exception:
            pass
        g.first_name_norm = _norm_name(g.first_name)
        g.last_name_norm = _norm_name(g.last_name)
        g.dob_iso = _norm_dob(g.dob)
        g.id_number_norm = _norm_id(g.id_number)
        g.identity_hash = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
        hit, score, tier = dnr_match(db, g)
        g.dnr_hit_id = hit.id if hit else None
        g.dnr_match_score = str(score) if score else None
        if hit:
            cur = str(g.remarks or "")
            if "dnr" not in cur.lower():
                g.remarks = ("DNR — " + cur).strip()
        db.commit()
        db.refresh(g)
    except Exception:
        pass
    return schemas.GuestOut.model_validate(g, from_attributes=True)


@app.post("/scan/duplex")
def scan_duplex(db=Depends(get_db)):
    """Scan ID front and back using physical scanner, then extract and save guest data."""
    import logging
    
    logging.info("Starting duplex scan...")
    
    try:
        device = _settings.get("scan_device")
        logging.info(f"Using scanner device: {device}")
        # This will show Windows scanner dialog - user scans front, then back
        front_bytes, back_bytes = scan_capture_duplex(device)
        logging.info(f"Scanner captured: front={len(front_bytes) if front_bytes else 0} bytes, back={len(back_bytes) if back_bytes else 0} bytes")
    except Exception as e:
        logging.error(f"Scanner capture failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scanner error: {e}. Make sure scanner is connected and drivers are installed.")
    
    # Validate and process front image
    try:
        imgf = Image.open(io.BytesIO(front_bytes)).convert('RGB')
        bf = io.BytesIO()
        imgf.save(bf, format='JPEG', quality=85)
        front_bytes = bf.getvalue()
        logging.info(f"Front image processed: {imgf.size[0]}x{imgf.size[1]}")
    except Exception as e:
        logging.error(f"Front image processing failed: {e}")
        raise HTTPException(status_code=500, detail="Scanner returned invalid front image")
    
    # Validate and process back image (if provided)
    if back_bytes:
        try:
            imgb = Image.open(io.BytesIO(back_bytes)).convert('RGB')
            bb = io.BytesIO()
            imgb.save(bb, format='JPEG', quality=85)
            back_bytes = bb.getvalue()
            logging.info(f"Back image processed: {imgb.size[0]}x{imgb.size[1]}")
        except Exception as e:
            logging.warning(f"Back image processing failed: {e}, continuing with front only")
            back_bytes = None

    # Save images (encrypted)
    fp_front_plain = filepaths.get_temp_image_path("front")
    fp_front_enc = filepaths.get_temp_encrypted_image_path("front")
    with open(fp_front_plain, "wb") as f:
        f.write(front_bytes)
    with open(fp_front_enc, "wb") as f:
        f.write(encrypt_bytes(front_bytes))

    fp_back_plain = None
    fp_back_enc = None
    if back_bytes:
        fp_back_plain = filepaths.get_temp_image_path("back")
        fp_back_enc = filepaths.get_temp_encrypted_image_path("back")
        with open(fp_back_plain, "wb") as f:
            f.write(back_bytes)
        with open(fp_back_enc, "wb") as f:
            f.write(encrypt_bytes(back_bytes))

    # Extract structured data using OCR
    logging.info("Starting OCR extraction...")
    logging.info("Starting OCR extraction...")
    try:
        from .ocr_utils import extract_structured_data_with_provider
        prov = _settings.get("ocr_provider")
        api_key = _settings.get("google_api_key")
        sd = extract_structured_data_with_provider(fp_front_plain, fp_back_plain, prov, api_key)
        logging.info(f"OCR extracted: first_name={sd.first_name}, last_name={sd.last_name}, dob={sd.date_of_birth}, id={sd.id_number}")
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        # Still create guest record even if OCR fails
        from .schemas import StructuredData
        sd = StructuredData()
    
    # Clean up temp plain images
    try:
        os.remove(fp_front_plain)
    except Exception:
        pass
    if fp_back_plain:
        try:
            os.remove(fp_back_plain)
        except Exception:
            pass

    # Create guest record
    g = models.Guest(
        first_name=sd.first_name,
        middle_name=sd.middle_name,
        last_name=sd.last_name,
        dob=iso_to_us_date(sd.date_of_birth),
        id_number=sd.id_number,
        expiration_date=iso_to_us_date(sd.expiration_date),
        issue_date=iso_to_us_date(sd.issue_date),
        address=sd.address,
        city=sd.city,
        state=sd.state,
        zip_code=sd.zip_code,
        nationality=sd.nationality,
        image_front_path=fp_front_enc,
        image_back_path=fp_back_enc,
        raw_text=sd.raw_text,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    logging.info(f"Guest record created: ID={g.id}")

    # Run DNR check
    try:
        from .dnr_manager import dnr_match, _norm_name, _norm_dob, _norm_id, identity_hash
        g.first_name_norm = _norm_name(g.first_name)
        g.last_name_norm = _norm_name(g.last_name)
        g.dob_iso = _norm_dob(g.dob)
        g.id_number_norm = _norm_id(g.id_number)
        g.identity_hash = identity_hash(g.first_name, g.last_name, g.dob, g.id_number)
        hit, score, tier = dnr_match(db, g)
        g.dnr_hit_id = hit.id if hit else None
        g.dnr_match_score = str(score) if score else None
        if hit:
            cur = str(g.remarks or "")
            if "dnr" not in cur.lower():
                g.remarks = ("DNR — " + cur).strip()
        db.commit()
        db.refresh(g)
        logging.info(f"DNR check completed: hit={hit is not None}, score={score}")
    except Exception as e:
        logging.warning(f"DNR check failed: {e}")
        db.commit()
        db.refresh(g)
    
    logging.info(f"Scan duplex completed successfully: guest_id={g.id}")
    return schemas.GuestOut.model_validate(g, from_attributes=True)
@app.post("/admin/repair-dates")
def admin_repair_dates(apply: bool = True, limit: int | None = None, request: Request = None, db=Depends(get_db)):
    try:
        get_current_admin(request)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin required")
    rows = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None)).order_by(models.Guest.created_at.asc())
    if limit:
        rows = rows.limit(int(limit))
    guests = rows.all()
    changed = []
    for g in guests:
        front_plain = None
        back_plain = None
        try:
            if g.image_front_path and os.path.exists(g.image_front_path):
                enc = open(g.image_front_path, "rb").read()
                dec = decrypt_bytes(enc)
                front_plain = filepaths.get_temp_image_path("front")
                open(front_plain, "wb").write(dec)
            if g.image_back_path and os.path.exists(g.image_back_path):
                enc2 = open(g.image_back_path, "rb").read()
                dec2 = decrypt_bytes(enc2)
                back_plain = filepaths.get_temp_image_path("back")
                open(back_plain, "wb").write(dec2)
            try:
                from .ocr_utils import extract_structured_data_with_provider
                prov = _settings.get("ocr_provider")
                api_key = _settings.get("google_api_key")
                sd = extract_structured_data_with_provider(front_plain, back_plain, prov, api_key)
            except Exception:
                sd = extract_structured_data(front_plain, back_plain)
            ndob = sd.date_of_birth or g.dob
            niss = sd.issue_date or g.issue_date
            nexp = sd.expiration_date or g.expiration_date
            ndob_iso = normalize_date_to_iso(ndob)
            niss_iso = normalize_date_to_iso(niss)
            nexp_iso = normalize_date_to_iso(nexp)
            try:
                validate_date_range(ndob_iso, niss_iso, nexp_iso)
            except Exception:
                continue
            ndob_us = iso_to_us_date(ndob_iso)
            niss_us = iso_to_us_date(niss_iso)
            nexp_us = iso_to_us_date(nexp_iso)
            if ndob_us != (g.dob or None) or niss_us != (g.issue_date or None) or nexp_us != (g.expiration_date or None):
                changed.append({"id": g.id, "prev": {"dob": g.dob, "issue": g.issue_date, "exp": g.expiration_date}, "next": {"dob": ndob_us, "issue": niss_us, "exp": nexp_us}})
                if apply:
                    g.dob = ndob_us
                    g.issue_date = niss_us
                    g.expiration_date = nexp_us
                    g.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    db.commit()
                    db.refresh(g)
        finally:
            for p in [front_plain, back_plain]:
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
    try:
        logging.info(json.dumps({"event": "repair_dates", "count": len(changed)}))
    except Exception:
        pass
    return {"status": "ok", "changed": changed, "count": len(changed), "applied": apply}


@app.post("/admin/migrate-us-dates")
def admin_migrate_us_dates(apply: bool = True, limit: int | None = None, request: Request = None, db=Depends(get_db)):
    try:
        get_current_admin(request)
    except Exception:
        raise HTTPException(status_code=403, detail="Admin required")
    rows = db.query(models.Guest).filter(models.Guest.deleted_at.is_(None)).order_by(models.Guest.created_at.asc())
    if limit:
        rows = rows.limit(int(limit))
    guests = rows.all()
    changed = []
    for g in guests:
        ndob = iso_to_us_date(g.dob)
        niss = iso_to_us_date(g.issue_date)
        nexp = iso_to_us_date(g.expiration_date)
        if ndob != g.dob or niss != g.issue_date or nexp != g.expiration_date:
            changed.append({"id": g.id, "prev": {"dob": g.dob, "issue": g.issue_date, "exp": g.expiration_date}, "next": {"dob": ndob, "issue": niss, "exp": nexp}})
            if apply:
                g.dob = ndob
                g.issue_date = niss
                g.expiration_date = nexp
                g.dob_iso = normalize_date_to_iso(ndob)
                g.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.commit()
                db.refresh(g)
    return {"status": "ok", "changed": changed, "count": len(changed), "applied": apply}
# Date utility functions are now imported from utils.date_utils
# This module provides: normalize_date_to_iso, iso_to_us_date, parse_iso_date, validate_date_range
