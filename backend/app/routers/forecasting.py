from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Item, Outlet
from ..services.forecasting import ForecastService

router = APIRouter()


@router.get("/forecast")
def get_forecast(item_id: int, outlet_id: int, horizon_days: int = 14, seasonal_period: int | None = 7, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    outlet = db.get(Outlet, outlet_id)
    if not item or not outlet:
        raise HTTPException(status_code=404, detail="Item or Outlet not found")

    points = ForecastService.forecast(db, item_id=item_id, outlet_id=outlet_id, horizon_days=horizon_days, seasonal_period=seasonal_period)
    return {
        "item_id": item_id,
        "outlet_id": outlet_id,
        "horizon_days": horizon_days,
        "points": [
            {"date": p.date.date().isoformat(), "forecast": p.forecast, "lower": p.lower, "upper": p.upper}
            for p in points
        ],
    }