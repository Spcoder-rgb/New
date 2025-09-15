import csv
import math
import random
from datetime import datetime, timedelta

random.seed(42)


def poisson(lmbda: float) -> int:
    # Knuth's algorithm for Poisson sampling
    if lmbda <= 0:
        return 0
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def write_csv(path: str, fieldnames: list[str], rows: list[dict]):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def generate_outlets(num_universities=3, outlets_per_uni=3):
    universities = [f"University_{i+1}" for i in range(num_universities)]
    rows = []
    outlet_id = 1
    for uni in universities:
        for j in range(outlets_per_uni):
            rows.append(
                {
                    "outlet_id": outlet_id,
                    "university": uni,
                    "outlet_name": f"{uni}_Outlet_{j+1}",
                    "cold_storage_capacity_kg": random.randint(200, 800),
                    "shelf_space_sqm": round(random.uniform(10, 60), 1),
                    "holding_cost_rate_per_day": round(random.uniform(0.001, 0.005), 4),
                }
            )
            outlet_id += 1
    return rows


def generate_items(num_packaged=25, num_raw=25):
    rows = []
    item_id = 1
    for i in range(num_packaged):
        rows.append(
            {
                "item_id": item_id,
                "item_name": f"Packaged_{i+1}",
                "category": "packaged",
                "unit": "unit",
                "unit_cost": round(random.uniform(0.5, 5.0), 2),
                "shelf_life_days": random.randint(90, 365),
            }
        )
        item_id += 1
    for i in range(num_raw):
        rows.append(
            {
                "item_id": item_id,
                "item_name": f"Raw_{i+1}",
                "category": "raw",
                "unit": "kg",
                "unit_cost": round(random.uniform(1.0, 10.0), 2),
                "shelf_life_days": random.randint(3, 21),
            }
        )
        item_id += 1
    return rows


def generate_events(start_date: str, end_date: str, universities: list[str]):
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    event_types = ["SportsFest", "CulturalFest", "Convocation", "Hackathon", "FoodFair"]
    rows = []
    for uni in universities:
        num_events = random.randint(6, 10)
        all_dates = list(daterange(start, end))
        event_dates = random.sample(all_dates, k=min(num_events, len(all_dates)))
        for d in sorted(event_dates):
            rows.append(
                {
                    "date": d.isoformat(),
                    "university": uni,
                    "event_name": random.choice(event_types),
                    "expected_demand_multiplier": round(random.uniform(1.3, 2.5), 2),
                }
            )
    return rows


def generate_sales(outlets: list[dict], items: list[dict], start_date: str, end_date: str, events: list[dict]):
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    event_index = {}
    for e in events:
        key = (e["date"], e["university"])
        event_index.setdefault(key, 1.0)
        event_index[key] = max(event_index[key], float(e["expected_demand_multiplier"]))

    rows = []
    max_cold = max(o["cold_storage_capacity_kg"] for o in outlets)
    for d in daterange(start, end):
        weekday_factor = 1.2 if d.weekday() < 5 else 1.0
        for o in outlets:
            event_mult = event_index.get((d.isoformat(), o["university"]), 1.0)
            outlet_scale = 0.6 + 0.4 * (o["cold_storage_capacity_kg"] / max_cold)
            for it in items:
                base = random.uniform(10, 60) if it["category"] == "packaged" else random.uniform(5, 40)
                mean = base * weekday_factor * event_mult * outlet_scale / 50.0
                qty = poisson(max(0.05, mean))
                if qty > 0:
                    price = round(float(it["unit_cost"]) * random.uniform(1.2, 1.8), 2)
                    rows.append(
                        {
                            "date": d.isoformat(),
                            "outlet_id": o["outlet_id"],
                            "item_id": it["item_id"],
                            "quantity_sold": qty,
                            "unit_price": price,
                        }
                    )
    return rows


def generate_inventory(outlets: list[dict], items: list[dict], start_date: str, end_date: str):
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    rows = []
    for d in daterange(start, end):
        for o in outlets:
            for it in items:
                avg_on_hand = random.uniform(10, 200) if it["category"] == "packaged" else random.uniform(5, 80)
                on_hand = max(0.0, random.gauss(avg_on_hand, avg_on_hand * 0.2))
                wastage_rate = random.uniform(0.005, 0.05) if it["category"] == "packaged" else random.uniform(0.02, 0.12)
                wastage_qty = 0
                if on_hand > 0:
                    # simple binomial approximation
                    trials = int(on_hand)
                    for _ in range(trials):
                        if random.random() < wastage_rate:
                            wastage_qty += 1
                days_to_expiry = random.randint(0, int(it["shelf_life_days"]))
                rows.append(
                    {
                        "date": d.isoformat(),
                        "outlet_id": o["outlet_id"],
                        "item_id": it["item_id"],
                        "on_hand_qty": round(on_hand, 2),
                        "wastage_qty": wastage_qty,
                        "days_to_expiry": days_to_expiry,
                    }
                )
    return rows


def main():
    start_date = (datetime.today().date() - timedelta(days=180)).isoformat()
    end_date = datetime.today().date().isoformat()

    outlets = generate_outlets(3, 3)
    items = generate_items(25, 25)
    universities = sorted({o["university"] for o in outlets})
    events = generate_events(start_date, end_date, universities)
    sales = generate_sales(outlets, items, start_date, end_date, events)
    inventory = generate_inventory(outlets, items, start_date, end_date)

    write_csv(
        "/workspace/data/raw/outlets.csv",
        [
            "outlet_id",
            "university",
            "outlet_name",
            "cold_storage_capacity_kg",
            "shelf_space_sqm",
            "holding_cost_rate_per_day",
        ],
        outlets,
    )
    write_csv(
        "/workspace/data/raw/items.csv",
        ["item_id", "item_name", "category", "unit", "unit_cost", "shelf_life_days"],
        items,
    )
    write_csv(
        "/workspace/data/raw/events.csv",
        ["date", "university", "event_name", "expected_demand_multiplier"],
        events,
    )
    write_csv(
        "/workspace/data/raw/sales.csv",
        ["date", "outlet_id", "item_id", "quantity_sold", "unit_price"],
        sales,
    )
    write_csv(
        "/workspace/data/raw/inventory.csv",
        ["date", "outlet_id", "item_id", "on_hand_qty", "wastage_qty", "days_to_expiry"],
        inventory,
    )

    print("Generated CSVs in /workspace/data/raw")


if __name__ == "__main__":
    main()

