"""
Date parsing and normalization utilities for IDSCNR.

Provides functions to parse, normalize, and validate dates from various formats
commonly found on ID documents.
"""
import re
from datetime import datetime, timezone
from typing import Optional


def normalize_date_to_iso(date_str: Optional[str]) -> Optional[str]:
    """Normalize a date string to ISO format (YYYY-MM-DD).
    
    Supports multiple input formats:
    - YYYY-MM-DD (already ISO)
    - MM/DD/YYYY or DD/MM/YYYY
    - Month DD, YYYY
    - YYYYMMDD
    - YYMMDD
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        ISO formatted date string (YYYY-MM-DD) or original string if parsing fails
    """
    if not date_str:
        return date_str
    
    t = str(date_str).strip()
    
    # Already ISO format
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", t)
    if m:
        return t
    
    # MM/DD/YYYY or DD/MM/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", t)
    if m:
        a, b, yy = int(m.group(1)), int(m.group(2)), m.group(3)
        y = int(yy)
        # If first token > 12 and second is valid month, treat as DD/MM
        if a > 12 and 1 <= b <= 12:
            year = y if len(yy) == 4 else (1900 + y if y >= 50 else 2000 + y)
            return f"{year:04d}-{b:02d}-{a:02d}"
        # Otherwise treat as MM/DD
        year = y if len(yy) == 4 else (1900 + y if y >= 50 else 2000 + y)
        return f"{year:04d}-{a:02d}-{b:02d}"
    
    # Month DD, YYYY (e.g., "January 15, 2024")
    m = re.match(r"^([A-Za-z]{3,9})\s+(\d{1,2}),\s*(\d{2,4})$", t)
    if m:
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        mm = months.get(m.group(1).lower()[:3], 0)
        dd = int(m.group(2))
        yy = m.group(3)
        y = int(yy)
        if mm:
            if len(yy) == 2:
                y = 1900 + y if y >= 50 else 2000 + y
            return f"{y:04d}-{mm:02d}-{dd:02d}"
    
    # YYYYMMDD
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    
    # YYMMDD (MRZ style)
    m = re.match(r"^(\d{2})(\d{2})(\d{2})$", t)
    if m:
        yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = 2000 + yy if yy <= 29 else 1900 + yy
        return f"{y:04d}-{mm:02d}-{dd:02d}"
    
    return t


def iso_to_us_date(iso_date: Optional[str]) -> Optional[str]:
    """Convert ISO date (YYYY-MM-DD) to US format (MM/DD/YYYY).
    
    Args:
        iso_date: ISO formatted date string
        
    Returns:
        US formatted date string (MM/DD/YYYY) or original string if conversion fails
    """
    if not iso_date:
        return iso_date
    
    iso = normalize_date_to_iso(iso_date)
    try:
        y, m, d = iso.split('-')
        return f"{m}/{d}/{y}"
    except Exception:
        return iso_date


def parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string to a datetime object.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        iso = normalize_date_to_iso(date_str)
        y, m, d = [int(x) for x in iso.split('-')]
        return datetime(y, m, d)
    except Exception:
        return None


def validate_date_range(
    dob: Optional[str],
    issue_date: Optional[str],
    expiration_date: Optional[str]
) -> None:
    """Validate that dates are in logical order.
    
    Validates:
    - DOB must be in the past
    - Issue date must be after DOB
    - Expiration date must be after issue date
    
    Args:
        dob: Date of birth
        issue_date: Issue date
        expiration_date: Expiration date
        
    Raises:
        ValueError: If date validation fails
    """
    from fastapi import HTTPException
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    dob_dt = parse_iso_date(dob)
    iss_dt = parse_iso_date(issue_date)
    exp_dt = parse_iso_date(expiration_date)
    
    if dob_dt and dob_dt > now:
        raise HTTPException(status_code=400, detail="Invalid DOB: date cannot be in the future")
    if iss_dt and dob_dt and iss_dt < dob_dt:
        raise HTTPException(status_code=400, detail="Invalid Issue date: must be after date of birth")
    if exp_dt and iss_dt and exp_dt < iss_dt:
        raise HTTPException(status_code=400, detail="Invalid Expiration date: must be after issue date")


