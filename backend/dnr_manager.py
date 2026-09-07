from typing import Optional, Tuple
from difflib import SequenceMatcher
import unicodedata
import re
from .models import Blacklist, Guest
from .security import verify_pin


def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def _norm_name(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    t = _strip_accents(s).lower()
    t = re.sub(r"[^a-z\s'-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _norm_dob(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        mm = int(m.group(1))
        dd = int(m.group(2))
        yy = m.group(3)
        year = int(yy)
        if len(yy) == 2:
            year = 1900 + year if year >= 50 else 2000 + year
        return f"{year:04d}-{mm:02d}-{dd:02d}"
    return s


def _norm_id(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    t = re.sub(r"[^A-Za-z0-9]", "", s).upper()
    return t


def identity_hash(first_name: Optional[str], last_name: Optional[str], dob: Optional[str], id_number: Optional[str]) -> str:
    nid = _norm_id(id_number)
    if nid:
        base = f"ID:{nid}"
    else:
        base = f"NM:{_norm_name(first_name) or ''}|{_norm_name(last_name) or ''}|DOB:{_norm_dob(dob) or ''}"
    import hashlib
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def dnr_match(db, guest: Guest) -> Tuple[Optional[Blacklist], float, int]:
    q = db.query(Blacklist)
    gid = _norm_id(guest.id_number)
    if gid:
        hit = q.filter(Blacklist.id_number_norm == gid).first()
        if hit:
            return hit, 1.0, 3

    gfn = _norm_name(guest.first_name)
    gln = _norm_name(guest.last_name)
    gdob = _norm_dob(guest.dob)
    if gfn and gln and gdob:
        candidates = (
            q.filter(Blacklist.dob_iso == gdob)
            .all()
        )
        best = None
        best_score = 0.0
        for c in candidates:
            s1 = SequenceMatcher(None, gfn or '', c.first_name_norm or '').ratio()
            s2 = SequenceMatcher(None, gln or '', c.last_name_norm or '').ratio()
            score = 0.5 * s1 + 0.5 * s2
            if score > best_score:
                best_score = score
                best = c
        if best and best_score >= 0.85:
            return best, best_score, 2
        if best and best_score >= 0.7:
            return best, best_score, 1
    return None, 0.0, 0


def check_dnr_match(db, guest: Guest) -> Optional[Blacklist]:
    hit, _, _ = dnr_match(db, guest)
    return hit


def verify_admin_pin(pin: Optional[str]) -> bool:
    return verify_pin(pin)