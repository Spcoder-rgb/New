import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


def generate_outlets(num_universities: int = 3, outlets_per_uni: int = 3) -> pd.DataFrame:
    universities = [f"University_{i+1}" for i in range(num_universities)]
    outlet_rows = []
    outlet_id = 1
    for uni in universities:
        for j in range(outlets_per_uni):
            outlet_rows.append(
                {
                    "outlet_id": outlet_id,
                    "university": uni,
                    "outlet_name": f"{uni}_Outlet_{j+1}",
                    "cold_storage_capacity_kg": int(np.random.randint(200, 800)),
                    "shelf_space_sqm": round(np.random.uniform(10, 60), 1),
                    "holding_cost_rate_per_day": round(np.random.uniform(0.001, 0.005), 4),
                    # daily holding rate as fraction of item value
                }
            )
            outlet_id += 1
    return pd.DataFrame(outlet_rows)


def generate_items(num_packaged: int = 20, num_raw: int = 20) -> pd.DataFrame:
    items = []
    item_id = 1
    for i in range(num_packaged):
        items.append(
            {
                "item_id": item_id,
                "item_name": f"Packaged_{i+1}",
                "category": "packaged",
                "unit": "unit",
                "unit_cost": round(np.random.uniform(0.5, 5.0), 2),
                "shelf_life_days": int(np.random.randint(90, 365)),
            }
        )
        item_id += 1
    for i in range(num_raw):
        items.append(
            {
                "item_id": item_id,
                "item_name": f"Raw_{i+1}",
                "category": "raw",
                "unit": "kg",
                "unit_cost": round(np.random.uniform(1.0, 10.0), 2),
                "shelf_life_days": int(np.random.randint(3, 21)),
            }
        )
        item_id += 1
    return pd.DataFrame(items)


def generate_events(start_date: str, end_date: str, universities: list[str]) -> pd.DataFrame:
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    days = (end - start).days + 1
    rows = []
    event_types = ["SportsFest", "CulturalFest", "Convocation", "Hackathon", "FoodFair"]
    for uni in universities:
        # sample 6-10 event days in the range
        num_events = int(np.random.randint(6, 11))
        event_dates = np.random.choice(pd.date_range(start, end), size=num_events, replace=False)
        for d in sorted(event_dates):
            rows.append(
                {
                    "date": d.date().isoformat(),
                    "university": uni,
                    "event_name": np.random.choice(event_types),
                    "expected_demand_multiplier": round(np.random.uniform(1.3, 2.5), 2),
                }
            )
    return pd.DataFrame(rows)


def generate_daily_sales(outlets: pd.DataFrame, items: pd.DataFrame, start_date: str, end_date: str, events: pd.DataFrame) -> pd.DataFrame:
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    dates = pd.date_range(start, end)

    # base demand by category
    base_packaged = np.random.uniform(10, 60, size=len(dates))
    base_raw = np.random.uniform(5, 40, size=len(dates))
    # weekly seasonality (higher on weekdays)
    weekday_factor = np.array([1.0 + 0.2 if d.weekday() < 5 else 1.0 for d in dates])

    events_index = events.set_index(["date", "university"]) if not events.empty else None

    sales_rows = []
    for _, outlet in outlets.iterrows():
        uni = outlet["university"]
        for dt_idx, dt in enumerate(dates):
            date_str = dt.date().isoformat()
            event_multiplier = 1.0
            if events_index is not None:
                key = (date_str, uni)
                if key in events_index.index:
                    # if multiple events same day, take max multiplier
                    event_multiplier = float(
                        events_index.loc[key]["expected_demand_multiplier"].max()
                        if isinstance(events_index.loc[key], pd.DataFrame)
                        else events_index.loc[key]["expected_demand_multiplier"]
                    )

            for _, item in items.iterrows():
                base = base_packaged[dt_idx] if item["category"] == "packaged" else base_raw[dt_idx]
                mean_demand = base * weekday_factor[dt_idx] * event_multiplier
                # item-specific popularity
                item_popularity = np.random.uniform(0.5, 1.5)
                # outlet scale factor (capacity proxy)
                outlet_scale = 0.6 + 0.4 * (outlet["cold_storage_capacity_kg"] / outlets["cold_storage_capacity_kg"].max())
                lam = max(0.1, mean_demand * item_popularity * outlet_scale / 50.0)
                qty = np.random.poisson(lam=lam)
                if qty > 0:
                    sales_rows.append(
                        {
                            "date": date_str,
                            "outlet_id": int(outlet["outlet_id"]),
                            "item_id": int(item["item_id"]),
                            "quantity_sold": int(qty),
                            "unit_price": float(round(item["unit_cost"] * np.random.uniform(1.2, 1.8), 2)),
                        }
                    )

    return pd.DataFrame(sales_rows)


def generate_inventory_positions(outlets: pd.DataFrame, items: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    dates = pd.date_range(start, end)
    rows = []
    for _, outlet in outlets.iterrows():
        for _, item in items.iterrows():
            # simulate average on-hand and wastage rates
            avg_daily_on_hand = np.random.uniform(10, 200) if item["category"] == "packaged" else np.random.uniform(5, 80)
            wastage_rate = np.random.uniform(0.005, 0.05) if item["category"] == "packaged" else np.random.uniform(0.02, 0.12)
            for dt in dates:
                date_str = dt.date().isoformat()
                on_hand = max(0.0, np.random.normal(loc=avg_daily_on_hand, scale=avg_daily_on_hand * 0.2))
                wastage_qty = np.random.binomial(n=int(on_hand), p=wastage_rate)
                days_to_expiry = int(np.random.randint(0, item["shelf_life_days"]))
                rows.append(
                    {
                        "date": date_str,
                        "outlet_id": int(outlet["outlet_id"]),
                        "item_id": int(item["item_id"]),
                        "on_hand_qty": round(on_hand, 2),
                        "wastage_qty": int(wastage_qty),
                        "days_to_expiry": days_to_expiry,
                    }
                )
    return pd.DataFrame(rows)


def main():
    start_date = (datetime.today() - timedelta(days=180)).date().isoformat()
    end_date = datetime.today().date().isoformat()

    outlets = generate_outlets(num_universities=3, outlets_per_uni=3)
    items = generate_items(num_packaged=25, num_raw=25)
    events = generate_events(start_date, end_date, universities=sorted(outlets["university"].unique().tolist()))
    sales = generate_daily_sales(outlets, items, start_date, end_date, events)
    inventory = generate_inventory_positions(outlets, items, start_date, end_date)

    # Save CSVs
    outlets.to_csv("/workspace/data/raw/outlets.csv", index=False)
    items.to_csv("/workspace/data/raw/items.csv", index=False)
    events.to_csv("/workspace/data/raw/events.csv", index=False)
    sales.to_csv("/workspace/data/raw/sales.csv", index=False)
    inventory.to_csv("/workspace/data/raw/inventory.csv", index=False)

    print("Generated datasets:")
    for p in [
        "/workspace/data/raw/outlets.csv",
        "/workspace/data/raw/items.csv",
        "/workspace/data/raw/events.csv",
        "/workspace/data/raw/sales.csv",
        "/workspace/data/raw/inventory.csv",
    ]:
        print(p)


if __name__ == "__main__":
    main()

