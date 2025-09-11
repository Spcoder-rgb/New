from __future__ import annotations

from datetime import date, timedelta

from backend.app.db import engine, Base, SessionLocal
from backend.app.models import University, Outlet, Supplier, Item, ItemBatch


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        uni = University(name="State University")
        db.add(uni)
        db.flush()

        outlet_a = Outlet(name="Main Canteen", university_id=uni.id)
        outlet_b = Outlet(name="Engineering Cafe", university_id=uni.id)
        db.add_all([outlet_a, outlet_b])

        sup = Supplier(name="FreshFoods Inc", lead_time_days=5, reliability_score=0.97, ordering_cost=40)
        db.add(sup)

        rice = Item(name="Rice", unit="kg", is_packaged=0, holding_cost_rate=0.2, default_lead_time_days=5, safety_stock=10)
        milk = Item(name="Milk 1L", unit="pack", is_packaged=1, holding_cost_rate=0.25, default_lead_time_days=3, safety_stock=5)
        chips = Item(name="Chips 50g", unit="pack", is_packaged=1, holding_cost_rate=0.3, default_lead_time_days=7, safety_stock=8)
        db.add_all([rice, milk, chips])
        db.flush()

        today = date.today()
        db.add_all([
            ItemBatch(item_id=rice.id, outlet_id=outlet_a.id, supplier_id=sup.id, quantity_purchased=100, quantity_remaining=100, unit_cost=1.2, purchase_date=today - timedelta(days=10), expiry_date=None),
            ItemBatch(item_id=milk.id, outlet_id=outlet_a.id, supplier_id=sup.id, quantity_purchased=50, quantity_remaining=50, unit_cost=0.8, purchase_date=today - timedelta(days=3), expiry_date=today + timedelta(days=4)),
            ItemBatch(item_id=chips.id, outlet_id=outlet_b.id, supplier_id=sup.id, quantity_purchased=200, quantity_remaining=200, unit_cost=0.3, purchase_date=today - timedelta(days=1), expiry_date=today + timedelta(days=60)),
        ])

        db.commit()
        print("Seed data inserted.")
    finally:
        db.close()


if __name__ == "__main__":
    main()