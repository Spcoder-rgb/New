import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class AppConfig:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:////workspace/data/inventory.db")
    env: str = os.getenv("ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    forecast_default_method: str = os.getenv("FORECAST_DEFAULT_METHOD", "arima")
    expiry_alert_days: int = int(os.getenv("EXPIRY_ALERT_DAYS", "7"))


def get_config() -> AppConfig:
    return AppConfig()