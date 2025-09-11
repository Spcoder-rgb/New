from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Tuple

from sqlalchemy.orm import Session

from ..models import ItemBatch, Transaction, TransactionLine, Consumption, TransactionType


class FIFOService:
    @staticmethod
    def get_available_batches(db: Session, item_id: int, outlet_id: int) -> List[ItemBatch]:
        return (
            db.query(ItemBatch)
            .filter(
                ItemBatch.item_id == item_id,
                ItemBatch.outlet_id == outlet_id,
                ItemBatch.quantity_remaining > 0,
            )
            .order_by(ItemBatch.purchase_date.asc(), ItemBatch.id.asc())
            .all()
        )

    @staticmethod
    def consume(db: Session, *, outlet_id: int, txn_type: TransactionType, lines: List[Tuple[int, float, float | None]], txn_date: datetime | None = None, notes: str | None = None) -> Transaction:
        txn = Transaction(outlet_id=outlet_id, txn_type=txn_type, txn_date=txn_date or datetime.utcnow(), notes=notes)
        db.add(txn)
        db.flush()

        for item_id, quantity, unit_price in lines:
            remaining_to_consume = float(quantity)
            while remaining_to_consume > 1e-9:
                batches = FIFOService.get_available_batches(db, item_id=item_id, outlet_id=outlet_id)
                if not batches:
                    raise ValueError(f"Insufficient stock for item {item_id} at outlet {outlet_id}")
                batch = batches[0]
                consume_qty = min(batch.quantity_remaining, remaining_to_consume)
                batch.quantity_remaining -= consume_qty
                db.add(batch)

                line = TransactionLine(
                    transaction_id=txn.id,
                    item_id=item_id,
                    quantity=consume_qty,
                    unit_price=unit_price,
                    batch_id=batch.id,
                )
                db.add(line)
                db.flush()

                db.add(
                    Consumption(
                        item_id=item_id,
                        outlet_id=outlet_id,
                        batch_id=batch.id,
                        transaction_line_id=line.id,
                        quantity=consume_qty,
                        consumption_type=txn_type,
                        consumption_date=txn.txn_date,
                    )
                )

                remaining_to_consume -= consume_qty

        db.commit()
        db.refresh(txn)
        return txn