from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Item, Outlet
from ..utils.analytics import (
    calculate_eoq,
    estimate_annual_demand,
    compute_reorder_point,
    get_current_stock,
    find_near_expiry_batches,
)

router = APIRouter()


@router.get("/eoq")
def eoq(item_id: int, outlet_id: int, ordering_cost: float | None = None, holding_cost_per_unit_year: float | None = None, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    outlet = db.get(Outlet, outlet_id)
    if not item or not outlet:
        raise HTTPException(status_code=404, detail="Item or Outlet not found")
    annual_demand = estimate_annual_demand(db, item_id=item_id, outlet_id=outlet_id)
    # If not provided, derive holding cost per unit per year from item holding_cost_rate and last unit_cost heuristic
    if holding_cost_per_unit_year is None:
        # crude heuristic: average unit cost from remaining batches
        from sqlalchemy import func
        from ..models import ItemBatch

        avg_cost = (
            db.query(func.coalesce(func.avg(ItemBatch.unit_cost), 0.0))
            .filter(ItemBatch.item_id == item_id, ItemBatch.outlet_id == outlet_id)
            .scalar()
        ) or 0.0
        holding_cost_per_unit_year = float(avg_cost) * float(item.holding_cost_rate)
    if ordering_cost is None:
        # default ordering cost fallback
        ordering_cost = 50.0
    value = calculate_eoq(annual_demand, ordering_cost, holding_cost_per_unit_year)
    return {"item_id": item_id, "outlet_id": outlet_id, "annual_demand": annual_demand, "eoq": value}


@router.get("/reorder_point")
def reorder_point(item_id: int, outlet_id: int, daily_demand: float | None = None, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    outlet = db.get(Outlet, outlet_id)
    if not item or not outlet:
        raise HTTPException(status_code=404, detail="Item or Outlet not found")
    if daily_demand is None:
        annual = estimate_annual_demand(db, item_id=item_id, outlet_id=outlet_id)
        daily_demand = annual / 365.0
    value = compute_reorder_point(daily_demand, lead_time_days=item.default_lead_time_days, safety_stock=item.safety_stock)
    stock = get_current_stock(db, item_id=item_id, outlet_id=outlet_id)
    return {"item_id": item_id, "outlet_id": outlet_id, "reorder_point": value, "current_stock": stock}


@router.get("/expiry_alerts")
def expiry_alerts(outlet_id: int, db: Session = Depends(get_db)):
    outlet = db.get(Outlet, outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    data = [
        {
            "batch_id": b.id,
            "item_id": b.item_id,
            "outlet_id": b.outlet_id,
            "quantity_remaining": b.quantity_remaining,
            "expiry_date": b.expiry_date,
            "days_left": days_left,
        }
        for b, days_left in find_near_expiry_batches(db, outlet_id=outlet_id)
    ]
    return {"outlet_id": outlet_id, "near_expiry": data}