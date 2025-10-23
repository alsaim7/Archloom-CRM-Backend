# models.py
from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint
from sqlalchemy import Column, Date, UniqueConstraint

class CustomerModel(SQLModel, table=True):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("customer_id", name="uq_customers_customer_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: str = Field(index=True, unique=True, nullable=False)
    fullname: str
    mobile: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default=None, nullable=True)
    address: str
    reg_date: date = Field(sa_column=Column(Date, nullable=False))
    note: Optional[str] = Field(default=None, nullable=True)
    status: str = Field(
        default="ACTIVE", index=True,
        description="Lead status: ACTIVE or OnHold or CLOSED",
    )
    hold_since: Optional[date] = Field(default=None, description="Date when HOLD started")

    # ✅ New: Foreign Key to User.id
    assigned_to: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        nullable=True
    )



class User(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    email: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    role: str = Field(default="employee", description="Role: employee | admin")

    # # ✅ Optional: relationship back to customers
    # customers: List["CustomerModel"] = Relationship(back_populates="user")