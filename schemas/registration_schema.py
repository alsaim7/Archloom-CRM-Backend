# schemas.py
import re
from datetime import date, datetime
from typing import List, Optional
from sqlmodel import SQLModel
from pydantic import EmailStr, field_validator



class NoteEntry(SQLModel):
    date: date
    note: str

class CustomerCreateSchema(SQLModel):
    fullname: str
    reg_date: date
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    address: str
    notes: List[NoteEntry] = []
    assigned_to: Optional[int] = None  # Add this line

    @field_validator("fullname", "address", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
        return v
    

    @field_validator("email", "mobile", mode="before")
    @classmethod
    def empty_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("mobile", mode="before")
    @classmethod
    def validate_mobile(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        cleaned_mobile = re.sub(r"\D", "", str(v))
        if not re.match(r"^\d{10}$", cleaned_mobile):
            raise ValueError("Mobile number must be exactly 10 digits")
        return cleaned_mobile

    @field_validator("reg_date", mode="before")
    @classmethod
    def validate_reg_date(cls, v):
        # PATCH: allow omission or empty -> None (i.e., no change when excluded_unset)
        if v in (None, ""):
            return None
        if isinstance(v, str):
            from datetime import datetime
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("reg_date must be in YYYY-MM-DD format")
        return v



class CustomerReadSchema(SQLModel):
    customer_id: str
    fullname: str
    reg_date: date
    mobile: Optional[str]
    email: Optional[str]
    address: str
    notes: List[NoteEntry] = []
    status: str
    hold_since: Optional[date]
    assigned_to_name: Optional[str] = None  # ✅ New field
    assigned_to: Optional[int] = None   # ✅ add this




# Update schema: all editable fields optional
class CustomerUpdateSchema(SQLModel):
    fullname: Optional[str] = None
    reg_date: Optional[date] = None  
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: List[NoteEntry] = []
    status: Optional[str] = "ACTIVE"
    hold_since: Optional[date] = None
    assigned_to: Optional[int] = None

    # Strip strings
    @field_validator("fullname", "address", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


    @field_validator("email", "mobile", mode="before")
    @classmethod
    def empty_email_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    # Validate mobile
    @field_validator("mobile", mode="before")
    @classmethod
    def validate_mobile(cls, v):
        if v in (None, ""):
            return None
        cleaned_mobile = re.sub(r"\D", "", str(v))
        if not re.match(r"^\d{10}$", cleaned_mobile):
            raise ValueError("Mobile number must be exactly 10 digits")
        return cleaned_mobile

    # Coerce dates
    @field_validator("reg_date", mode="before")
    @classmethod
    def validate_reg_date(cls, v):
        # PATCH: allow omission or empty -> None (i.e., no change when excluded_unset)
        if v in (None, ""):
            return None
        if isinstance(v, str):
            from datetime import datetime
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("reg_date must be in YYYY-MM-DD format")
        return v

    @field_validator("hold_since", mode="before")
    @classmethod
    def validate_hold_since(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("hold_since must be in YYYY-MM-DD format")
        return v
    