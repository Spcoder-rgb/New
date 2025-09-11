from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class TransactionType(str, Enum):
    purchase = "purchase"
    sale = "sale"
    wastage = "wastage"


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    outlets: Mapped[List[Outlet]] = relationship(back_populates="university", cascade="all, delete-orphan")


class Outlet(Base):
    __tablename__ = "outlets"
    __table_args__ = (
        UniqueConstraint("university_id", "name", name="uq_outlet_university_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)

    university: Mapped[University] = relationship(back_populates="outlets")
    batches: Mapped[List[ItemBatch]] = relationship(back_populates="outlet", cascade="all, delete-orphan")
    transactions: Mapped[List[Transaction]] = relationship(back_populates="outlet", cascade="all, delete-orphan")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    ordering_cost: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    prices: Mapped[List[SupplierItemPrice]] = relationship(back_populates="supplier", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="unit", nullable=False)
    is_packaged: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)  # 0/1 for SQLite compat
    holding_cost_rate: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)  # annual fraction
    default_lead_time_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    safety_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    batches: Mapped[List[ItemBatch]] = relationship(back_populates="item", cascade="all, delete-orphan")
    prices: Mapped[List[SupplierItemPrice]] = relationship(back_populates="item", cascade="all, delete-orphan")


class SupplierItemPrice(Base):
    __tablename__ = "supplier_item_prices"
    __table_args__ = (
        UniqueConstraint("supplier_id", "item_id", name="uq_supplier_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    supplier: Mapped[Supplier] = relationship(back_populates="prices")
    item: Mapped[Item] = relationship(back_populates="prices")


class ItemBatch(Base):
    __tablename__ = "item_batches"
    __table_args__ = (
        Index("ix_item_batches_item_outlet", "item_id", "outlet_id"),
        CheckConstraint("quantity_purchased >= 0"),
        CheckConstraint("quantity_remaining >= 0"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))

    quantity_purchased: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_remaining: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)

    purchase_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    item: Mapped[Item] = relationship(back_populates="batches")
    outlet: Mapped[Outlet] = relationship(back_populates="batches")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_outlet_date", "outlet_id", "txn_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
    txn_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    txn_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    outlet: Mapped[Outlet] = relationship(back_populates="transactions")
    lines: Mapped[List[TransactionLine]] = relationship(back_populates="transaction", cascade="all, delete-orphan")


class TransactionLine(Base):
    __tablename__ = "transaction_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[Optional[float]] = mapped_column(Float)  # purchase cost or sale price
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("item_batches.id", ondelete="SET NULL"))

    transaction: Mapped[Transaction] = relationship(back_populates="lines")
    batch: Mapped[Optional[ItemBatch]] = relationship()


class Consumption(Base):
    __tablename__ = "consumptions"
    __table_args__ = (
        CheckConstraint("quantity >= 0"),
        Index("ix_consumptions_item_outlet_date", "item_id", "outlet_id", "consumption_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id", ondelete="CASCADE"), nullable=False)
    batch_id: Mapped[int] = mapped_column(ForeignKey("item_batches.id", ondelete="CASCADE"), nullable=False)
    transaction_line_id: Mapped[int] = mapped_column(ForeignKey("transaction_lines.id", ondelete="CASCADE"), nullable=False)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    consumption_type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    consumption_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)