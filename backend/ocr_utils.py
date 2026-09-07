import os
import json
import base64
import time
from collections import deque
import re
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError
from typing import Optional
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from datetime import datetime
import pytesseract
from pyzbar.pyzbar import decode
from dataclasses import dataclass


def extract_text_tesseract(image_path: str) -> str:
    """Extract text from ID image using Tesseract OCR with enhanced preprocessing.
    
    Uses multiple preprocessing techniques and PSM modes to improve accuracy.
    """
    import logging
    
    try:
        img = Image.open(image_path)
    except Exception as e:
        logging.error(f"Failed to open image {image_path}: {e}")
        return ""
    
    texts_with_scores = []
    
    # Convert to grayscale
    try:
        gray = img.convert('L')
    except Exception as e:
        logging.warning(f"Failed to convert to grayscale: {e}")
        gray = img
    
    # Upscale if too small (improves OCR accuracy)
    w, h = gray.size
    if max(w, h) < 2000:
        scale = 2000 / max(w, h)
        try:
            gray = gray.resize((int(w*scale), int(h*scale)), Image.Resampling.LANCZOS)
        except Exception:
            gray = gray.resize((int(w*scale), int(h*scale)))
    
    # Try multiple preprocessing approaches
    variants_to_try = []
    
    # Variant 1: Autocontrast + sharpening (most reliable)
    try:
        variant1 = ImageOps.autocontrast(gray)
        variant1 = variant1.filter(ImageFilter.SHARPEN)
        variants_to_try.append(('autocontrast_sharp', variant1))
    except Exception:
        pass
    
    # Variant 2: Enhanced contrast
    try:
        enhancer = ImageEnhance.Contrast(gray)
        variant2 = enhancer.enhance(1.5)
        variant2 = ImageOps.autocontrast(variant2)
        variants_to_try.append(('enhanced_contrast', variant2))
    except Exception:
        pass
    
    # Variant 3: Simple threshold (fallback)
    try:
        variant3 = ImageOps.autocontrast(gray)
        variant3 = variant3.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        variants_to_try.append(('simple_thresh', variant3))
    except Exception:
        pass
    
    # Also try original grayscale
    variants_to_try.append(('original_gray', gray))
    
    # Try different PSM modes
    psm_modes = [6, 11, 7]  # Start with most reliable ones
    
    # Try each preprocessing variant with each PSM mode
    for variant_name, processed_img in variants_to_try:
        for psm in psm_modes:
            try:
                cfg = f'--oem 3 --psm {psm} -l eng'
                # Get text with confidence scores
                data = pytesseract.image_to_data(processed_img, config=cfg, output_type=pytesseract.Output.DICT)
                
                # Extract text and calculate average confidence
                text_parts = []
                confidences = []
                for i, word in enumerate(data.get('text', [])):
                    word_str = str(word).strip()
                    conf = int(data.get('conf', [0])[i]) if i < len(data.get('conf', [])) else 0
                    if word_str and conf > 0:
                        text_parts.append(word_str)
                        confidences.append(conf)
                
                text = ' '.join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                if text.strip():
                    texts_with_scores.append((text, avg_confidence, len(text.strip()), variant_name, psm))
            except Exception as e:
                logging.debug(f"OCR attempt failed: variant={variant_name}, psm={psm}, error={e}")
                continue
    
    # Select best result based on confidence and length
    if texts_with_scores:
        # Sort by confidence (weighted) and length
        texts_with_scores.sort(key=lambda x: (x[1] * 0.7 + min(x[2] / 100, 1) * 30, x[2]), reverse=True)
        best_text = texts_with_scores[0][0]
        
        # Log which variant worked best
        best_variant_info = texts_with_scores[0]
        logging.info(f"OCR best result: variant={best_variant_info[3]}, psm={best_variant_info[4]}, confidence={best_variant_info[1]:.1f}, length={best_variant_info[2]}")
        logging.debug(f"OCR extracted text preview: {best_text[:200]}")
        
        return best_text
    
    # Fallback: simple extraction
    try:
        logging.warning("Using fallback OCR extraction")
        result = pytesseract.image_to_string(img, config='--oem 3 --psm 6 -l eng') or ""
        if result:
            logging.info(f"Fallback OCR extracted {len(result)} characters")
        return result
    except Exception as e:
        logging.error(f"OCR extraction completely failed: {e}")
        return ""


def parse_aamva_from_barcode(image_path: str) -> dict:
    # Many US DL have PDF417 barcodes with AAMVA data
    # Try original orientation and common rotations; scaling can help decoding
    def try_decode(img: Image.Image):
        try:
            codes = decode(img)
            for code in codes:
                if code.type == "PDF417":
                    raw = code.data.decode(errors="ignore")
                    return _parse_aamva_text(raw)
        except Exception:
            return None
        return None

    try:
        base = Image.open(image_path)
        attempts = []
        attempts.extend([base, base.rotate(90, expand=True), base.rotate(180, expand=True), base.rotate(270, expand=True)])
        w, h = base.size
        for s in [1.5, 2.0]:
            attempts.append(base.resize((int(w*s), int(h*s))))
        for candidate in attempts:
            g = ImageOps.autocontrast(candidate.convert('L')).convert('RGB')
            parsed = try_decode(g)
            if parsed:
                return parsed
    except Exception:
        pass
    return {}


def _parse_aamva_text(raw: str) -> dict:
    # Simplified AAMVA parser: look for common fields
    # Keys often include: DCS (Last Name), DCT (First Name), DAC (First Name), DAD (Middle Name), DBB (DOB YYYYMMDD), DAU (Height), DAA (Full Name), DBD (Issue date), DBA (Expiration), DCS/DAC
    data = {}
    def get(tag: str) -> Optional[str]:
        idx = raw.find(tag)
        if idx == -1:
            return None
        val = raw[idx+3:]
        # value until next tag prefix starting with 'D'
        for stop in ["\nD", "\rD"]:
            sidx = val.find(stop)
            if sidx != -1:
                return val[:sidx].strip()
        return val.strip()

    ln = get("DCS")
    fn = get("DAC") or get("DCT")
    mn = get("DAD")
    dob = get("DBB")
    exp = get("DBA")
    iss = get("DBD")
    address1 = get("DAG")
    city = get("DAI")
    state = get("DAJ")
    zipc = get("DAK")
    idn = get("DAQ")

    # Convert DOB like YYYYMMDD to ISO
    def fmt_date(s: Optional[str]) -> Optional[str]:
        if not s or len(s) < 8:
            return s
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

    out = {
        "last_name": ln,
        "first_name": fn,
        "middle_name": mn,
        "date_of_birth": fmt_date(dob),
        "expiration_date": fmt_date(exp),
        "issue_date": fmt_date(iss),
        "address": address1,
        "city": city,
        "state": state,
        "zip_code": zipc,
        "id_number": idn,
    }
    # ID type heuristic based on content
    lower = raw.lower()
    if any(k in lower for k in ["driver", "driving license", "dl"]):
        out["id_type"] = "Driving License"
    elif "passport" in lower:
        out["id_type"] = "Passport"
    return out


def parse_fields_from_text(text: str) -> dict:
    # Heuristic parsing for passports and IDs when barcode unavailable
    out = {"raw_text": text}
    # Pre-split lines for positional heuristics
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    # Helper: clean name value by removing leading numeric markers like "1" or "2" and punctuation
    def clean_name(val: str | None) -> Optional[str]:
        if not val:
            return None
        s = val.strip()
        # Remove common OCR artifacts
        s = re.sub(r'[|\\/]', ' ', s)  # Replace common OCR mistakes
        s = re.sub(r'\s+', ' ', s)  # Normalize whitespace
        tokens = [t for t in s.split() if t]
        # Drop leading tokens that are purely numbers like "1", "2", "1." or "#2"
        while tokens and re.fullmatch(r"[#]?\d+\.?", tokens[0]):
            tokens.pop(0)
        if not tokens:
            return None
        # Pick the first token that contains letters; strip surrounding punctuation
        for t in tokens:
            # Remove OCR artifacts like |, \, /, etc.
            t2 = re.sub(r"^[^A-Za-z]+|[^A-Za-z'\-]+$", "", t)
            t2 = re.sub(r'[|\\/]', '', t2)  # Remove common OCR mistakes
            if re.search(r"[A-Za-z]", t2) and len(t2) >= 2:  # At least 2 letters
                # Capitalize first letter, rest lowercase (common name format)
                return t2[0].upper() + t2[1:].lower() if len(t2) > 1 else t2.upper()
        # Fallback: return first token if it has any letters
        if tokens:
            first = re.sub(r'[^A-Za-z\'\-]', '', tokens[0])
            if len(first) >= 2:
                return first[0].upper() + first[1:].lower() if len(first) > 1 else first.upper()
        return None
    # Name patterns
    name_match = re.search(r"\bName[:\s]*([A-Z][A-Za-z'\-]+)\s+([A-Z][A-Za-z'\-]+)\b", text, re.IGNORECASE)
    if name_match:
        out["first_name"] = clean_name(name_match.group(1))
        out["last_name"] = clean_name(name_match.group(2))
    else:
        # Many US DLs use numbered labels: "1 LAST" and "2 FIRST" (dot optional)
        de_last = re.search(r"\b1\.?[\s]*([A-Z][A-Z'\-]{2,})\b", text)
        de_first = re.search(r"\b2\.?[\s]+([A-Z][A-Za-z'\-]{2,})\b", text)
        if de_last and de_first:
            out["last_name"] = clean_name(de_last.group(1))
            out["first_name"] = clean_name(de_first.group(1))
        else:
        # "LAST, FIRST" format
            comma_match = re.search(r"\b([A-Z][A-Za-z'\-]{2,})\s*,\s*([A-Z][A-Za-z'\-]{2,})\b", text)
            if comma_match:
                out["last_name"] = clean_name(comma_match.group(1))
                out["first_name"] = clean_name(comma_match.group(2))
            else:
                # Explicit label formats: First/Last/Given/Surname
                fn_label = re.search(r"\b(First Name|Given Name|Given Names)[:\s]*([A-Z][A-Za-z '\-]{2,})\b", text)
                ln_label = re.search(r"\b(Last Name|Surname|Family Name)[:\s]*([A-Z][A-Za-z '\-]{2,})\b", text)
                if fn_label and ln_label:
                    out["first_name"] = clean_name(fn_label.group(2))
                    out["last_name"] = clean_name(ln_label.group(2))
                else:
                    # If only "2 FIRST" exists, try to infer last name from nearby uppercase token
                    if de_first and not de_last and "last_name" not in out:
                        # Locate the line index of the "2 FIRST" marker
                        idx2 = None
                        for i, ln in enumerate(lines):
                            if re.search(r"\b2\.?\b", ln) and de_first.group(1) in ln:
                                idx2 = i
                                break
                        # Find a previous line that is a single uppercase word (non-stopword)
                        if idx2 is not None:
                            name_stop = {"DRIVER", "LICENSE", "IDENTIFICATION", "CARD", "DELAWARE", "GEORGIA", "USA", "ADDRESS", "CITY", "STATE", "ZIP", "NORTH", "CAROLINA", "MILITARY", "SAMPLE", "NOT", "FOR", "FEDERAL", "PURPOSES", "PROBATIONARY", "LIMITED", "TERM", "WISCONSIN", "FORWARD"}
                            for j in range(idx2 - 1, max(-1, idx2 - 5), -1):
                                if j < 0:
                                    break
                                cand = lines[j].strip()
                                if re.fullmatch(r"[A-Z][A-Z'\-]{2,}", cand) and cand not in name_stop:
                                    out["last_name"] = clean_name(cand)
                                    out.setdefault("first_name", clean_name(de_first.group(1)))
                                    break
                    # Single-line uppercase names (e.g., LAST FIRST MIDDLE)
                    # Avoid picking headings like "DRIVER LICENSE" or state names
                    stopwords = {"DRIVER", "LICENSE", "IDENTIFICATION", "CARD", "DELAWARE", "GEORGIA", "USA", "ADDRESS", "CITY", "STATE", "ZIP", "NORTH", "CAROLINA", "MILITARY", "SAMPLE", "NOT", "FOR", "FEDERAL", "PURPOSES", "PROBATIONARY", "LIMITED", "TERM", "WISCONSIN", "FORWARD"}
                    for ln in text.splitlines():
                        s = ln.strip()
                        # two or three uppercase words without digits
                        if re.fullmatch(r"[A-Z][A-Z'\- ]{2,}", s) and not any(ch.isdigit() for ch in s):
                            tokens = [t for t in s.split() if t and t.upper() not in stopwords and not re.fullmatch(r"\d+", t)]
                            if 2 <= len(tokens) <= 3:
                                # Many IDs list LAST then FIRST
                                out.setdefault("last_name", clean_name(tokens[0]))
                                out.setdefault("first_name", clean_name(tokens[1]))
                                if len(tokens) == 3:
                                    out.setdefault("middle_name", clean_name(tokens[2]))
                                break
                    # Passport MRZ (e.g., P<USAERIKSON<<ANNA<MARIA)
                    mrz_line1 = None
                    mrz_line2 = None
                    lines_all = [ln.strip().replace(' ', '') for ln in text.splitlines() if ln.strip()]
                    for i, ln in enumerate(lines_all):
                        if ln.startswith("P<") and "<<" in ln:
                            mrz_line1 = ln
                            # second line usually follows and is 40-44 chars of A-Z0-9<
                            if i + 1 < len(lines_all) and re.fullmatch(r"[A-Z0-9<]{40,}", lines_all[i+1]):
                                mrz_line2 = lines_all[i+1]
                            break
                    if mrz_line1:
                        try:
                            name_section = mrz_line1[mrz_line1.find("<", 2)+1:]
                            name_section = name_section.replace("<", " ").strip()
                            tokens = [t for t in name_section.split() if t]
                            if tokens:
                                out.setdefault("last_name", clean_name(tokens[0]))
                                if len(tokens) > 1:
                                    out.setdefault("first_name", clean_name(tokens[1]))
                                if len(tokens) > 2:
                                    out.setdefault("middle_name", clean_name(" ".join(tokens[2:])))
                        except Exception:
                            pass
                    # Parse DOB and expiry from MRZ line 2 (TD3 passport)
                    if mrz_line2 and len(mrz_line2) >= 27:
                        try:
                            dob_raw = mrz_line2[14:20]
                            exp_raw = mrz_line2[22:28]
                            def _yyMMdd_to_iso(s: str, kind: str) -> str | None:
                                if not re.fullmatch(r"\d{6}", s):
                                    return None
                                yy = int(s[0:2]); mm = int(s[2:4]); dd = int(s[4:6])
                                if not (1 <= mm <= 12 and 1 <= dd <= 31):
                                    return None
                                # MRZ pivot: 00-29 -> 2000+, 30-99 -> 1900+
                                year = 2000 + yy if yy <= 29 else 1900 + yy
                                # Validate realistic ranges: DOB in past, EXP in future
                                try:
                                    dt = datetime(year, mm, dd)
                                except Exception:
                                    return None
                                if kind == 'dob':
                                    if dt > datetime.now():
                                        year = 1900 + yy
                                else:
                                    if dt < datetime.now():
                                        year = 2000 + yy
                                try:
                                    datetime(year, mm, dd)
                                except Exception:
                                    return None
                                return f"{year:04d}-{mm:02d}-{dd:02d}"
                            dob_iso = _yyMMdd_to_iso(dob_raw, 'dob')
                            exp_iso = _yyMMdd_to_iso(exp_raw, 'exp')
                            if dob_iso:
                                out.setdefault("date_of_birth", dob_iso)
                            if exp_iso:
                                out.setdefault("expiration_date", exp_iso)
                        except Exception:
                            pass
                    else:
                        # Try consecutive uppercase lines anywhere (common on DLs)
                        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                        def is_upper_name(s: str) -> bool:
                            if not (bool(re.fullmatch(r"[A-Z][A-Z'\- ]{2,}", s)) and 1 <= len(s.split()) <= 3 and not any(ch.isdigit() for ch in s)):
                                return False
                            toks = [t for t in s.split() if t]
                            name_stop = {"DRIVER", "LICENSE", "IDENTIFICATION", "CARD", "DELAWARE", "GEORGIA", "USA", "ADDRESS", "CITY", "STATE", "ZIP", "NORTH", "CAROLINA", "MILITARY", "SAMPLE", "NOT", "FOR", "FEDERAL", "PURPOSES", "PROBATIONARY", "LIMITED", "TERM", "WISCONSIN", "FORWARD"}
                            return all(t.upper() not in name_stop for t in toks)
                        for i in range(max(0, len(lines)-1)):
                            if is_upper_name(lines[i]) and is_upper_name(lines[i+1]):
                                out["last_name"] = clean_name(lines[i].split()[0])
                                out["first_name"] = clean_name(lines[i+1].split()[0])
                                break
    dob_match = re.search(r"(DOB|Birth)[^0-9]*([0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4})", text, re.IGNORECASE)
    if dob_match:
        out["date_of_birth"] = dob_match.group(2)
    # ID number patterns (support variations like "DL No." or "DL NUMBER")
    id_match = re.search(
        r"\b(?:DLN|DL(?:\s*(?:NO\.?|NUMBER)\s*)?|LIC(?:\s*(?:NO\.?|NUMBER)\s*)?|ID(?:\s*(?:#|NO\.?|NUMBER)\s*)?|Identifier|Customer\s*Identifier|Passport|Document\s*(?:No\.?|Number))\s*[:#\-]*\s*([A-Z0-9]{6,})\b",
        text,
        re.IGNORECASE,
    )
    if id_match:
        # Use the first capturing group which holds the ID value
        out["id_number"] = id_match.group(1)
    else:
        # OCR quirk: some fonts render "ID NO" as "ON"
        on_match = re.search(r"\bON\s+(\d{6,})\b", text)
        if on_match:
            out.setdefault("id_number", on_match.group(1))
        else:
            # Prefer tokens before CLASS label (common WI format like 4P340-8670-2385-079 CLASS D)
            pre_class = re.search(r"\b([A-Z0-9][A-Z0-9\-]{8,})\b\s+CLASS\b", text)
            if pre_class:
                out.setdefault("id_number", pre_class.group(1))
            else:
                # Fallback to any long alphanumeric (favor tokens containing digits or hyphens)
                # First, try hyphenated ID-like tokens
                hyphens = re.findall(r"\b([A-Z0-9][A-Z0-9\-]{8,})\b", text)
                def _good_id(tok: str) -> bool:
                    if len(tok) < 6:
                        return False
                    # Must contain at least one digit and not be pure digits (to avoid ZIP)
                    if not any(ch.isdigit() for ch in tok):
                        return False
                    if tok.isdigit():
                        return False
                    sw = {
                        "SAMPLE", "DRIVER", "LICENSE", "DELAWARE", "GEORGIA", "USA", "INSTRUCTIONAL", "PERMIT", "LIMITED", "TERM",
                        "UNDER", "CLASS", "SEX", "EYES", "HGT", "WGT", "DL", "NOT", "FOR", "FEDERAL", "PURPOSES", "WISCONSIN", "FORWARD"
                    }
                    if re.fullmatch(r"[A-Z]\d{7}", tok):
                        return True
                    return tok.upper() not in sw
                candidate = None
                for tok in hyphens:
                    if _good_id(tok):
                        candidate = tok
                        break
                if not candidate:
                    # Then try simple alphanumeric tokens
                    generic = re.findall(r"\b([A-Z0-9]{6,})\b", text)
                    for tok in generic:
                        if _good_id(tok):
                            candidate = tok
                            break
                if candidate:
                    out.setdefault("id_number", candidate)
    # Expiration / Issue / DOB with more date formats
    exp_match = re.search(r"(EXP|Expiry|Expiration|Exp)[^0-9A-Za-z]*([0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{2,4})", text, re.IGNORECASE)
    if exp_match:
        out["expiration_date"] = exp_match.group(2)
    # If multiple dates appear around Exp label (e.g., next line), choose the latest
    def _collect_dates(s: str) -> list[str]:
        return re.findall(r"\b(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{2,4})\b", s)
    for i, ln in enumerate(lines):
        if re.search(r"\b(EXP|Expiry|Expiration|Exp)\b", ln, re.IGNORECASE):
            # Consider same line and the immediate next line
            cands = _collect_dates(ln)
            if i + 1 < len(lines):
                cands += _collect_dates(lines[i+1])
            if cands:
                # Normalize then pick lexicographically max (ISO)
                iso = []
                for d in cands:
                    nd = re.sub(r"\s+", " ", d).strip()
                    # Will be normalized by norm_date below
                    iso.append(nd)
                # Apply normalization first
                def _norms(ds: list[str]) -> list[str]:
                    outd = []
                    for x in ds:
                        nx = x
                        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", x)
                        if m:
                            a, b, yy = int(m.group(1)), int(m.group(2)), m.group(3)
                            year = int(yy)
                            if len(yy) == 2:
                                year = 1900 + year if year >= 50 else 2000 + year
                            # Interpret as DD/MM if first token >12, else MM/DD
                            mm, dd = (b, a) if a > 12 and 1 <= b <= 12 else (a, b)
                            nx = f"{year:04d}-{mm:02d}-{dd:02d}"
                        outd.append(nx)
                    return outd
                norms = _norms(iso)
                latest = sorted(norms)[-1]
                out["expiration_date"] = latest
    iss_match = re.search(r"(Issue|Issued|Iss)[^0-9A-Za-z]*([0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4}|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{2,4})", text, re.IGNORECASE)
    if iss_match:
        out["issue_date"] = iss_match.group(2)
    # DOB can appear as MM/DD/YYYY, YYYY-MM-DD or Month DD, YYYY
    dob_match2 = re.search(r"\b([0-9]{2}/[0-9]{2}/[0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[A-Za-z]{3,9}\s+\d{1,2},\s*\d{2,4})\b", text)
    if dob_match2 and "date_of_birth" not in out:
        out["date_of_birth"] = dob_match2.group(1)
    # Address: prefer line before City, State ZIP; strip leading label digits
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        city_state = re.match(r"^([A-Za-z][A-Za-z\s]+),\s*([A-Z]{2})\s*([0-9]{5})", ln)
        if city_state:
            out["city"] = city_state.group(1).strip()
            out["state"] = city_state.group(2).strip()
            out["zip_code"] = city_state.group(3).strip()
            if i > 0:
                addr_line = re.sub(r"^[#]?\d+\s+", "", lines[i-1])
                addr_line = re.sub(r"\s{2,}", " ", addr_line).strip()
                out.setdefault("address", addr_line)
            break
    nationality_match = re.search(r"Nationality[:\s]*([A-Za-z\s]+)", text, re.IGNORECASE)
    if nationality_match:
        out["nationality"] = nationality_match.group(1).strip()
    # Normalize dates to ISO (YYYY-MM-DD) when possible
    def norm_date(s: str | None) -> str | None:
        if not s:
            return s
        s = s.strip()
        # DD/MM/YYYY when first token >12 and valid
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
        if m:
            d1, d2, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if d1 > 12 and 1 <= d2 <= 12 and 1900 <= y <= 2100:
                try:
                    datetime(y, d2, d1)
                    return f"{y:04d}-{d2:02d}-{d1:02d}"
                except Exception:
                    pass
        # MM/DD/YYYY or MM/DD/YY
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
        if m:
            mm, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
            year = int(yy)
            if not (1 <= mm <= 12 and 1 <= dd <= 31):
                return s
            if len(yy) == 2:
                year = 1900 + year if year >= 50 else 2000 + year
            return f"{year:04d}-{mm:02d}-{dd:02d}"
        # DD/MM/YYYY (non-US style) when first token clearly day (>12)
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
        if m:
            d1, d2, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if d1 > 12 and 1 <= d2 <= 12 and 1900 <= y <= 2100:
                try:
                    datetime(y, d2, d1)
                    return f"{y:04d}-{d2:02d}-{d1:02d}"
                except Exception:
                    pass
        # YYYY-MM-DD
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
        if m:
            return s
        # YYYYMMDD
        m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
        if m:
            y, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                datetime(y, mm, dd)
                return f"{y:04d}-{mm:02d}-{dd:02d}"
            except Exception:
                return s
        # YYMMDD (MRZ style)
        m = re.match(r"^(\d{2})(\d{2})(\d{2})$", s)
        if m:
            yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                year = 2000 + yy if yy <= 29 else 1900 + yy
                try:
                    datetime(year, mm, dd)
                    return f"{year:04d}-{mm:02d}-{dd:02d}"
                except Exception:
                    return s
        # Month DD, YYYY
        m = re.match(r"^([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{2,4})$", s)
        if m:
            months = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            }
            mm = months.get(m.group(1).lower()[:3], 0)
            dd = int(m.group(2))
            yy = m.group(3)
            year = int(yy)
            if len(yy) == 2:
                year = 1900 + year if year >= 50 else 2000 + year
            if mm:
                return f"{year:04d}-{mm:02d}-{dd:02d}"
        return s

    if out.get("date_of_birth"):
        out["date_of_birth"] = norm_date(out["date_of_birth"]) or out["date_of_birth"]
    if out.get("expiration_date"):
        out["expiration_date"] = norm_date(out["expiration_date"]) or out["expiration_date"]
    if out.get("issue_date"):
        out["issue_date"] = norm_date(out["issue_date"]) or out["issue_date"]

    # Infer ID type
    lower = text.lower()
    if any(k in lower for k in ["driver", "driving license", "dl"]):
        out["id_type"] = "Driving License"
    elif "passport" in lower:
        out["id_type"] = "Passport"
    elif "identification" in lower:
        out["id_type"] = "Identification Card"
    return out


def extract_structured_data(front_path: str, back_path: Optional[str]):
    """Extract structured data from ID images using Tesseract OCR.
    
    Args:
        front_path: Path to front image of ID
        back_path: Optional path to back image of ID
    """
    import logging
    
    # First try barcode on front/back (many DLs have barcode on back)
    fields = {}
    try:
        if front_path:
            fields = parse_aamva_from_barcode(front_path)
            if fields:
                logging.info(f"Barcode data from front: {list(fields.keys())}")
    except Exception as e:
        logging.warning(f"Barcode parsing from front failed: {e}")
    
    if back_path:
        try:
            back_fields = parse_aamva_from_barcode(back_path)
            if back_fields:
                logging.info(f"Barcode data from back: {list(back_fields.keys())}")
            for k, v in back_fields.items():
                if k not in fields or not fields[k]:
                    fields[k] = v
        except Exception as e:
            logging.warning(f"Barcode parsing from back failed: {e}")
    
    # Always use Tesseract for OCR
    text = ""
    parsed = {}
    try:
        if front_path:
            text = extract_text_tesseract(front_path)
            logging.info(f"OCR extracted {len(text)} characters from front")
            if text:
                parsed = parse_fields_from_text(text)
                logging.info(f"Parsed fields from front: {list(parsed.keys())}")
    except Exception as e:
        logging.error(f"OCR extraction from front failed: {e}")
    
    # Merge barcode fields (prefer barcode)
    combined = {**parsed, **{k: v for k, v in fields.items() if v}}
    
    # Log what we found
    if combined:
        logging.info(f"Combined extracted data: first_name={combined.get('first_name')}, last_name={combined.get('last_name')}, dob={combined.get('date_of_birth')}")
    else:
        logging.warning("No data extracted from OCR or barcode!")
    
    def _iso(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        return parse_fields_from_text.__globals__['re'].match(r'^\d{4}-\d{2}-\d{2}$', s) and s or None
    
    def _norm(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        return (parse_fields_from_text.__globals__['re'].match(r'^\d{4}-\d{2}-\d{2}$', s) and s) or None
    
    def _to_iso(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        x = s.strip()
        m = parse_fields_from_text.__globals__['re'].match(r'^(\d{4})-(\d{2})-(\d{2})$', x)
        if m:
            return x
        m = parse_fields_from_text.__globals__['re'].match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', x)
        if m:
            a, b, yy = int(m.group(1)), int(m.group(2)), m.group(3)
            y = int(yy)
            if a > 12 and 1 <= b <= 12:
                y = y if len(yy)==4 else (1900+y if y>=50 else 2000+y)
                return f"{y:04d}-{b:02d}-{a:02d}"
            y = y if len(yy)==4 else (1900+y if y>=50 else 2000+y)
            return f"{y:04d}-{a:02d}-{b:02d}"
        m = parse_fields_from_text.__globals__['re'].match(r'^(\d{4})(\d{2})(\d{2})$', x)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = parse_fields_from_text.__globals__['re'].match(r'^(\d{2})(\d{2})(\d{2})$', x)
        if m:
            yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y = 2000+yy if yy<=29 else 1900+yy
            return f"{y:04d}-{mm:02d}-{dd:02d}"
        return None
    
    def _age_ok(iso: Optional[str]) -> bool:
        if not iso:
            return False
        try:
            y, m, d = [int(x) for x in iso.split('-')]
            dt = datetime(y, m, d)
            now = datetime.now()
            yrs = (now - dt).days / 365.25
            return 18 <= yrs <= 120
        except Exception:
            return False
    
    dob_bar = fields.get('date_of_birth')
    dob_txt = parsed.get('date_of_birth')
    dob_bar_iso = _to_iso(dob_bar) if dob_bar else None
    dob_txt_iso = _to_iso(dob_txt) if dob_txt else None
    if dob_bar_iso and not _age_ok(dob_bar_iso) and _age_ok(dob_txt_iso):
        combined['date_of_birth'] = dob_txt
    
    # If back image provided, try additional text
    if back_path:
        try:
            back_text = extract_text_tesseract(back_path)
            logging.info(f"OCR extracted {len(back_text)} characters from back")
            if back_text:
                back_parsed = parse_fields_from_text(back_text)
                logging.info(f"Parsed fields from back: {list(back_parsed.keys())}")
                for k, v in back_parsed.items():
                    if k not in combined or not combined[k]:
                        combined[k] = v
        except Exception as e:
            logging.warning(f"Back image OCR failed: {e}")
    
    # Store raw text from front (most important)
    raw_text_to_store = text if text else (combined.get("raw_text") or "")
    
    # Final logging
    logging.info(f"Final extracted data - first_name: {combined.get('first_name')}, last_name: {combined.get('last_name')}, dob: {combined.get('date_of_birth')}, id: {combined.get('id_number')}")
    
    from .schemas import StructuredData
    return StructuredData(
        first_name=combined.get("first_name"),
        middle_name=combined.get("middle_name"),
        last_name=combined.get("last_name"),
        date_of_birth=combined.get("date_of_birth"),
        id_number=combined.get("id_number"),
        expiration_date=combined.get("expiration_date"),
        issue_date=combined.get("issue_date"),
        id_type=combined.get("id_type"),
        address=combined.get("address"),
        city=combined.get("city"),
        state=combined.get("state"),
        zip_code=combined.get("zip_code"),
        nationality=combined.get("nationality"),
        raw_text=raw_text_to_store,
    )


def extract_text_google(image_path: str, api_key: str) -> str:
    import base64, json, urllib.request
    with open(image_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("ascii")
    payload = {
        "requests": [
            {
                "image": {"content": content_b64},
                "features": [{"type": "TEXT_DETECTION"}],
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read()
    obj = json.loads(body.decode("utf-8"))
    try:
        ann = obj["responses"][0]
        if "textAnnotations" in ann and ann["textAnnotations"]:
            return ann["textAnnotations"][0].get("description", "") or ""
        if "fullTextAnnotation" in ann:
            return ann["fullTextAnnotation"].get("text", "") or ""
    except Exception:
        pass
    return ""


def extract_structured_data_with_provider(front_path: str, back_path: Optional[str], provider: Optional[str], api_key: Optional[str]):
    import logging
    fields = {}
    try:
        if front_path:
            fields = parse_aamva_from_barcode(front_path)
            if fields:
                logging.info(f"Barcode data from front: {list(fields.keys())}")
    except Exception as e:
        logging.warning(f"Barcode parsing from front failed: {e}")
    if back_path:
        try:
            back_fields = parse_aamva_from_barcode(back_path)
            if back_fields:
                logging.info(f"Barcode data from back: {list(back_fields.keys())}")
            for k, v in back_fields.items():
                if k not in fields or not fields[k]:
                    fields[k] = v
        except Exception as e:
            logging.warning(f"Barcode parsing from back failed: {e}")
    text = ""
    parsed = {}
    try:
        if front_path:
            if provider == "google" and api_key:
                text = extract_text_google(front_path, api_key)
            else:
                text = extract_text_tesseract(front_path)
            logging.info(f"OCR({provider or 'tesseract'}) extracted {len(text)} characters from front")
            if text:
                parsed = parse_fields_from_text(text)
                logging.info(f"Parsed fields from front: {list(parsed.keys())}")
    except Exception as e:
        logging.error(f"OCR extraction from front failed: {e}")
    combined = {**parsed, **{k: v for k, v in fields.items() if v}}
    def _to_iso(s: Optional[str]) -> Optional[str]:
        if not s:
            return None
        x = s.strip()
        import re as _re
        m = _re.match(r'^(\d{4})-(\d{2})-(\d{2})$', x)
        if m:
            return x
        m = _re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', x)
        if m:
            a, b, yy = int(m.group(1)), int(m.group(2)), m.group(3)
            y = int(yy)
            if a > 12 and 1 <= b <= 12:
                y = y if len(yy)==4 else (1900+y if y>=50 else 2000+y)
                return f"{y:04d}-{b:02d}-{a:02d}"
            y = y if len(yy)==4 else (1900+y if y>=50 else 2000+y)
            return f"{y:04d}-{a:02d}-{b:02d}"
        m = _re.match(r'^(\d{4})(\d{2})(\d{2})$', x)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = _re.match(r'^(\d{2})(\d{2})(\d{2})$', x)
        if m:
            yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y = 2000+yy if yy<=29 else 1900+yy
            return f"{y:04d}-{mm:02d}-{dd:02d}"
        return None
    def _age_ok(iso: Optional[str]) -> bool:
        if not iso:
            return False
        try:
            y, m, d = [int(x) for x in iso.split('-')]
            from datetime import datetime as _dt
            dt = _dt(y, m, d)
            now = _dt.now()
            yrs = (now - dt).days / 365.25
            return 18 <= yrs <= 120
        except Exception:
            return False
    dob_bar = fields.get('date_of_birth')
    dob_txt = parsed.get('date_of_birth')
    dob_bar_iso = _to_iso(dob_bar) if dob_bar else None
    dob_txt_iso = _to_iso(dob_txt) if dob_txt else None
    if dob_bar_iso and not _age_ok(dob_bar_iso) and _age_ok(dob_txt_iso):
        combined['date_of_birth'] = dob_txt
    if back_path:
        try:
            if provider == "google" and api_key:
                back_text = extract_text_google(back_path, api_key)
            else:
                back_text = extract_text_tesseract(back_path)
            logging.info(f"OCR({provider or 'tesseract'}) extracted {len(back_text)} characters from back")
            if back_text:
                back_parsed = parse_fields_from_text(back_text)
                logging.info(f"Parsed fields from back: {list(back_parsed.keys())}")
                for k, v in back_parsed.items():
                    if k not in combined or not combined[k]:
                        combined[k] = v
        except Exception as e:
            logging.warning(f"Back image OCR failed: {e}")
    raw_text_to_store = text if text else (combined.get("raw_text") or "")
    logging.info(f"Final extracted data - first_name: {combined.get('first_name')}, last_name: {combined.get('last_name')}, dob: {combined.get('date_of_birth')}, id: {combined.get('id_number')}")
    from .schemas import StructuredData
    return StructuredData(
        first_name=combined.get("first_name"),
        middle_name=combined.get("middle_name"),
        last_name=combined.get("last_name"),
        date_of_birth=combined.get("date_of_birth"),
        id_number=combined.get("id_number"),
        expiration_date=combined.get("expiration_date"),
        issue_date=combined.get("issue_date"),
        id_type=combined.get("id_type"),
        address=combined.get("address"),
        city=combined.get("city"),
        state=combined.get("state"),
        zip_code=combined.get("zip_code"),
        nationality=combined.get("nationality"),
        raw_text=raw_text_to_store,
    )
