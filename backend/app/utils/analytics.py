from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import get_config
from ..models import Item, Outlet, ItemBatch, Consumption, TransactionType


def calculate_eoq(annual_demand_units: float, ordering_cost: float, holding_cost_per_unit_per_year: float) -> float:
    if annual_demand_units <= 0 or ordering_cost <= 0 or holding_cost_per_unit_per_year <= 0:
        return 0.0
    # Wilson EOQ formula: sqrt((2DS)/H)
    from math import sqrt

    return float(sqrt((2.0 * annual_demand_units * ordering_cost) / holding_cost_per_unit_per_year))


def estimate_annual_demand(db: Session, item_id: int, outlet_id: int) -> float:
    # Sum last 365 days consumption (sale only) and annualize
    one_year_ago = func.datetime(func.now(), "-365 days")
    result = (
        db.query(func.coalesce(func.sum(Consumption.quantity), 0.0))
        .filter(
            Consumption.item_id == item_id,
            Consumption.outlet_id == outlet_id,
            Consumption.consumption_type == TransactionType.sale,
            Consumption.consumption_date >= one_year_ago,
        )
        .scalar()
    )
    return float(result or 0.0)


def compute_reorder_point(daily_demand: float, lead_time_days: int, safety_stock: float) -> float:
    return max(0.0, daily_demand * float(lead_time_days) + safety_stock)


def get_current_stock(db: Session, item_id: int, outlet_id: int) -> float:
    qty = (
        db.query(func.coalesce(func.sum(ItemBatch.quantity_remaining), 0.0))
        .filter(ItemBatch.item_id == item_id, ItemBatch.outlet_id == outlet_id)
        .scalar()
    )
    return float(qty or 0.0)


def find_near_expiry_batches(db: Session, outlet_id: int) -> List[Tuple[ItemBatch, int]]:
    config = get_config()
    today = date.today()
    cutoff = today + timedelta(days=config.expiry_alert_days)
    batches = (
        db.query(ItemBatch)
        .filter(
            ItemBatch.outlet_id == outlet_id,
            ItemBatch.expiry_date.isnot(None),
            ItemBatch.expiry_date <= cutoff,
            ItemBatch.quantity_remaining > 0,
        )
        .order_by(ItemBatch.expiry_date.asc())
        .all()
    )
    return [(b, (b.expiry_date - today).days if b.expiry_date else 0) for b in batches]