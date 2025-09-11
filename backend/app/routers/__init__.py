from .health import router as health
from .core import router as core
from .transactions import router as transactions
from .analytics import router as analytics
from .suggestions import router as suggestions
from .forecasting import router as forecasting

__all__ = ["health", "core", "transactions", "analytics", "suggestions", "forecasting"]