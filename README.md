## Food Inventory Management System (Universities)

This project provides a Python backend (FastAPI + SQLAlchemy) and a Streamlit dashboard for managing food inventory across university outlets.

### Features
- Inventory transactions (purchase, sales, wastage) with FIFO batch consumption
- Analytics: EOQ, holding cost, reorder points, expiry alerts
- Demand forecasting (ARIMA by default; Prophet optional)
- Outlet-wise and university-wise comparisons, packaged vs raw performance
- Auto purchase-order suggestions and near-expiry alerts

### Quickstart
1. Create a Python 3.10+ virtual env and install dependencies:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy environment file and adjust if needed:
```bash
cp .env.example .env
```

3. Run the API:
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000/docs` for interactive docs.

4. Seed sample data (optional):
```bash
python scripts/seed_data.py
```

5. Run the Streamlit dashboard:
```bash
streamlit run dashboard/app.py --server.port 8501
```

### Configuration
- Configure database via `DATABASE_URL` in `.env`. Defaults to a local SQLite file at `data/inventory.db`.
- Prophet is optional and heavy. If desired, install `prophet` and the required build toolchain, then enable Prophet in forecasting settings.

### Notes
- This is a reference implementation. Adjust models and parameters (e.g., holding cost rates, lead times, safety stock) to your real-world context.