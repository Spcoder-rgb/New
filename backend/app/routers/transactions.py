from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Item, Outlet, ItemBatch, TransactionType
from ..schemas.core import TransactionCreate, TransactionRead
from ..services.fifo import FIFOService

router = APIRouter()


@router.post("/transactions", response_model=TransactionRead)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    outlet = db.get(Outlet, payload.outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if payload.txn_type == TransactionType.purchase:
        created_batches = []
        for line in payload.lines:
            item = db.get(Item, line.item_id)
            if not item:
                raise HTTPException(status_code=404, detail=f"Item {line.item_id} not found")
            if line.unit_price is None:
                raise HTTPException(status_code=400, detail="unit_price required for purchase line")
            batch = ItemBatch(
                item_id=line.item_id,
                outlet_id=payload.outlet_id,
                supplier_id=None,
                quantity_purchased=line.quantity,
                quantity_remaining=line.quantity,
                unit_cost=line.unit_price,
                purchase_date=payload.txn_date.date() if payload.txn_date else date.today(),
                expiry_date=None,
            )
            db.add(batch)
            created_batches.append(batch)
        db.commit()
        # Represent purchase as transaction with lines mapping to batches (optional). For now, return a synthesized response via FIFOService by creating a transaction with zero consumption lines isn't ideal.
        # To keep it simple, create a no-consumption transaction with lines referencing no batch.
        from ..models import Transaction, TransactionLine

        txn = Transaction(outlet_id=payload.outlet_id, txn_type=payload.txn_type, txn_date=payload.txn_date)
        db.add(txn)
        db.flush()
        for line in payload.lines:
            db.add(TransactionLine(transaction_id=txn.id, item_id=line.item_id, quantity=line.quantity, unit_price=line.unit_price))
        db.commit()
        db.refresh(txn)
        return txn

    elif payload.txn_type in (TransactionType.sale, TransactionType.wastage):
        lines = [(l.item_id, l.quantity, l.unit_price) for l in payload.lines]
        txn = FIFOService.consume(
            db,
            outlet_id=payload.outlet_id,
            txn_type=payload.txn_type,
            lines=lines,
            txn_date=payload.txn_date,
            notes=payload.notes,
        )
        return txn

    else:
        raise HTTPException(status_code=400, detail="Unsupported transaction type")