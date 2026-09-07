from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.types import Text
from sqlalchemy.orm import validates
from .database import Base
from .security import encrypt_str, decrypt_str
from datetime import datetime


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(Text, nullable=True)
    middle_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    dob = Column(Text, nullable=True)  # ISO date string
    id_number = Column(Text, nullable=True)
    expiration_date = Column(Text, nullable=True)
    issue_date = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    zip_code = Column(Text, nullable=True)
    nationality = Column(Text, nullable=True)
    phone_country_code = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=True)
    room_number = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    image_front_path = Column(Text, nullable=True)
    image_back_path = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    dnr_hit_id = Column(Integer, nullable=True)
    dnr_match_score = Column(String, nullable=True)
    dnr_match_tier = Column(Integer, nullable=True)
    dnr_override_by = Column(Text, nullable=True)
    dnr_override_reason = Column(Text, nullable=True)
    dnr_override_at = Column(DateTime, nullable=True)

    first_name_norm = Column(Text, nullable=True)
    last_name_norm = Column(Text, nullable=True)
    dob_iso = Column(Text, nullable=True)
    id_number_norm = Column(Text, nullable=True)
    identity_hash = Column(Text, nullable=True)


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    dob = Column(Text, nullable=True)
    id_number = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    first_name_norm = Column(Text, nullable=True)
    last_name_norm = Column(Text, nullable=True)
    dob_iso = Column(Text, nullable=True)
    id_number_norm = Column(Text, nullable=True)