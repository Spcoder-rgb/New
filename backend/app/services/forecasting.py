from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from statsmodels.tsa.statespace.sarimax import SARIMAX

from ..models import Consumption, TransactionType


@dataclass
class ForecastPoint:
    date: pd.Timestamp
    forecast: float
    lower: float
    upper: float


class ForecastService:
    @staticmethod
    def load_daily_series(db: Session, item_id: int, outlet_id: int, start_days_ago: int = 365) -> pd.Series:
        # Aggregate daily sales quantities
        rows = (
            db.query(
                func.date(Consumption.consumption_date).label("d"),
                func.sum(Consumption.quantity).label("qty"),
            )
            .filter(
                Consumption.item_id == item_id,
                Consumption.outlet_id == outlet_id,
                Consumption.consumption_type == TransactionType.sale,
                Consumption.consumption_date >= func.datetime(func.now(), f"-{start_days_ago} days"),
            )
            .group_by("d")
            .order_by("d")
            .all()
        )
        if not rows:
            return pd.Series(dtype=float)
        df = pd.DataFrame(rows, columns=["date", "qty"])  # type: ignore[arg-type]
        df["date"] = pd.to_datetime(df["date"])  # ensure timestamp
        df = df.set_index("date").asfreq("D", fill_value=0.0)
        return df["qty"].astype(float)

    @staticmethod
    def forecast_arima(series: pd.Series, horizon_days: int = 14, seasonal_period: Optional[int] = 7) -> List[ForecastPoint]:
        if series.empty:
            # return flat zero forecast
            today = pd.Timestamp(datetime.utcnow().date())
            return [ForecastPoint(date=today + pd.Timedelta(days=i + 1), forecast=0.0, lower=0.0, upper=0.0) for i in range(horizon_days)]

        order = (1, 1, 1)
        seasonal_order = (1, 1, 1, seasonal_period) if seasonal_period else (0, 0, 0, 0)
        model = SARIMAX(series, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
        result = model.fit(disp=False)
        forecast_res = result.get_forecast(steps=horizon_days)
        mean = forecast_res.predicted_mean.clip(lower=0.0)
        conf_int = forecast_res.conf_int(alpha=0.2)  # 80% intervals
        lower = np.maximum(0.0, conf_int.iloc[:, 0])
        upper = np.maximum(lower, conf_int.iloc[:, 1])

        points: List[ForecastPoint] = []
        for i, d in enumerate(mean.index):
            points.append(
                ForecastPoint(
                    date=pd.Timestamp(d),
                    forecast=float(mean.iloc[i]),
                    lower=float(lower.iloc[i]),
                    upper=float(upper.iloc[i]),
                )
            )
        return points

    @staticmethod
    def forecast(db: Session, *, item_id: int, outlet_id: int, horizon_days: int = 14, seasonal_period: Optional[int] = 7) -> List[ForecastPoint]:
        series = ForecastService.load_daily_series(db, item_id=item_id, outlet_id=outlet_id, start_days_ago=365)
        return ForecastService.forecast_arima(series, horizon_days=horizon_days, seasonal_period=seasonal_period)