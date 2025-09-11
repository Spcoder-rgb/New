from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    purchase = "purchase"
    sale = "sale"
    wastage = "wastage"


class UniversityCreate(BaseModel):
    name: str


class UniversityRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class OutletCreate(BaseModel):
    name: str
    university_id: int


class OutletRead(BaseModel):
    id: int
    name: str
    university_id: int

    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    name: str
    lead_time_days: int = 7
    reliability_score: float = 0.95
    ordering_cost: float = 50.0


class SupplierRead(BaseModel):
    id: int
    name: str
    lead_time_days: int
    reliability_score: float
    ordering_cost: float

    class Config:
        from_attributes = True


class ItemCreate(BaseModel):
    name: str
    unit: str = "unit"
    is_packaged: bool = False
    holding_cost_rate: float = 0.25
    default_lead_time_days: int = 7
    safety_stock: float = 0.0


class ItemRead(BaseModel):
    id: int
    name: str
    unit: str
    is_packaged: bool
    holding_cost_rate: float
    default_lead_time_days: int
    safety_stock: float

    class Config:
        from_attributes = True


class ItemBatchCreate(BaseModel):
    item_id: int
    outlet_id: int
    supplier_id: Optional[int] = None
    quantity_purchased: float
    unit_cost: float
    purchase_date: date
    expiry_date: Optional[date] = None


class ItemBatchRead(BaseModel):
    id: int
    item_id: int
    outlet_id: int
    supplier_id: Optional[int]
    quantity_purchased: float
    quantity_remaining: float
    unit_cost: float
    purchase_date: date
    expiry_date: Optional[date]

    class Config:
        from_attributes = True


class TransactionLineCreate(BaseModel):
    item_id: int
    quantity: float
    unit_price: Optional[float] = None


class TransactionCreate(BaseModel):
    outlet_id: int
    txn_type: TransactionType
    txn_date: Optional[datetime] = None
    notes: Optional[str] = None
    lines: list[TransactionLineCreate]


class TransactionLineRead(BaseModel):
    id: int
    item_id: int
    quantity: float
    unit_price: Optional[float]
    batch_id: Optional[int]

    class Config:
        from_attributes = True


class TransactionRead(BaseModel):
    id: int
    outlet_id: int
    txn_type: TransactionType
    txn_date: datetime
    notes: Optional[str]
    lines: list[TransactionLineRead]

    class Config:
        from_attributes = True