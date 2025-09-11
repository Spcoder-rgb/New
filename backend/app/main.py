from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from .db import engine, Base
from .routers import health, core, transactions, analytics, suggestions, forecasting


app = FastAPI(title="University Food Inventory Management API", default_response_class=ORJSONResponse)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


# Routers
app.include_router(health, prefix="/health", tags=["health"])
app.include_router(core, prefix="/api", tags=["core"])
app.include_router(transactions, prefix="/api", tags=["transactions"])
app.include_router(analytics, prefix="/api/analytics", tags=["analytics"])
app.include_router(suggestions, prefix="/api", tags=["suggestions"])
app.include_router(forecasting, prefix="/api/forecasting", tags=["forecasting"])