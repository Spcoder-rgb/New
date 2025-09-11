from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import University, Outlet, Supplier, Item, ItemBatch
from ..schemas.core import (
    UniversityCreate,
    UniversityRead,
    OutletCreate,
    OutletRead,
    SupplierCreate,
    SupplierRead,
    ItemCreate,
    ItemRead,
    ItemBatchCreate,
    ItemBatchRead,
)

router = APIRouter()


# Universities
@router.post("/universities", response_model=UniversityRead)
def create_university(payload: UniversityCreate, db: Session = Depends(get_db)):
    existing = db.query(University).filter(University.name == payload.name).one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="University already exists")
    obj = University(name=payload.name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/universities", response_model=list[UniversityRead])
def list_universities(db: Session = Depends(get_db)):
    return db.query(University).order_by(University.name).all()


# Outlets
@router.post("/outlets", response_model=OutletRead)
def create_outlet(payload: OutletCreate, db: Session = Depends(get_db)):
    university = db.get(University, payload.university_id)
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    existing = (
        db.query(Outlet)
        .filter(Outlet.university_id == payload.university_id, Outlet.name == payload.name)
        .one_or_none()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Outlet already exists for university")
    obj = Outlet(name=payload.name, university_id=payload.university_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/outlets", response_model=list[OutletRead])
def list_outlets(db: Session = Depends(get_db)):
    return db.query(Outlet).order_by(Outlet.id).all()


# Suppliers
@router.post("/suppliers", response_model=SupplierRead)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    existing = db.query(Supplier).filter(Supplier.name == payload.name).one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier already exists")
    obj = Supplier(
        name=payload.name,
        lead_time_days=payload.lead_time_days,
        reliability_score=payload.reliability_score,
        ordering_cost=payload.ordering_cost,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/suppliers", response_model=list[SupplierRead])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).order_by(Supplier.name).all()


# Items
@router.post("/items", response_model=ItemRead)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    existing = db.query(Item).filter(Item.name == payload.name).one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Item already exists")
    obj = Item(
        name=payload.name,
        unit=payload.unit,
        is_packaged=1 if payload.is_packaged else 0,
        holding_cost_rate=payload.holding_cost_rate,
        default_lead_time_days=payload.default_lead_time_days,
        safety_stock=payload.safety_stock,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/items", response_model=list[ItemRead])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).order_by(Item.name).all()


# Batches
@router.post("/batches", response_model=ItemBatchRead)
def create_batch(payload: ItemBatchCreate, db: Session = Depends(get_db)):
    item = db.get(Item, payload.item_id)
    outlet = db.get(Outlet, payload.outlet_id)
    if not item or not outlet:
        raise HTTPException(status_code=404, detail="Item or Outlet not found")

    obj = ItemBatch(
        item_id=payload.item_id,
        outlet_id=payload.outlet_id,
        supplier_id=payload.supplier_id,
        quantity_purchased=payload.quantity_purchased,
        quantity_remaining=payload.quantity_purchased,
        unit_cost=payload.unit_cost,
        purchase_date=payload.purchase_date,
        expiry_date=payload.expiry_date,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/batches", response_model=list[ItemBatchRead])
def list_batches(db: Session = Depends(get_db)):
    return db.query(ItemBatch).order_by(ItemBatch.id.desc()).limit(500).all()