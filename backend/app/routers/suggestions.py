from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Item, Outlet
from ..utils.analytics import estimate_annual_demand, compute_reorder_point, get_current_stock

router = APIRouter()


@router.get("/purchase_suggestions")
def purchase_suggestions(outlet_id: int, item_id: int, db: Session = Depends(get_db)):
    outlet = db.get(Outlet, outlet_id)
    item = db.get(Item, item_id)
    if not outlet or not item:
        raise HTTPException(status_code=404, detail="Item or Outlet not found")

    annual = estimate_annual_demand(db, item_id=item_id, outlet_id=outlet_id)
    daily = annual / 365.0
    r = compute_reorder_point(daily, item.default_lead_time_days, item.safety_stock)
    stock = get_current_stock(db, item_id=item_id, outlet_id=outlet_id)

    quantity_to_order = max(0.0, r - stock)
    return {
        "outlet_id": outlet_id,
        "item_id": item_id,
        "reorder_point": r,
        "current_stock": stock,
        "suggested_order_qty": quantity_to_order,
    }