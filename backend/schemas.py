from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class StructuredData(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    id_number: Optional[str] = None
    expiration_date: Optional[str] = None
    issue_date: Optional[str] = None
    id_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    nationality: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    raw_text: Optional[str] = None


class GuestBase(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    id_number: Optional[str] = None
    expiration_date: Optional[str] = None
    issue_date: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    nationality: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    room_number: Optional[str] = None
    remarks: Optional[str] = None
    raw_text: Optional[str] = None


class GuestOut(GuestBase):
    id: int
    image_front_path: Optional[str] = None
    image_back_path: Optional[str] = None
    created_at: Optional[datetime] = None
    dnr_hit_id: Optional[int] = None
    dnr_match_score: Optional[str] = None
    dnr_match_tier: Optional[int] = None
    dnr_override_by: Optional[str] = None
    dnr_override_reason: Optional[str] = None
    dnr_override_at: Optional[datetime] = None
    first_name_norm: Optional[str] = None
    last_name_norm: Optional[str] = None
    dob_iso: Optional[str] = None
    id_number_norm: Optional[str] = None
    identity_hash: Optional[str] = None
    
    # Enable Pydantic v2 attribute-based validation for from_orm usage
    model_config = ConfigDict(from_attributes=True)


class GuestUpdate(BaseModel):
    # Allow editing of all guest fields
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    id_number: Optional[str] = None
    expiration_date: Optional[str] = None
    issue_date: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    nationality: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    room_number: Optional[str] = None
    remarks: Optional[str] = None
    override_dnr: bool = False


# Legacy scan schemas removed; StructuredData retained for OCR utils compatibility