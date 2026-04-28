"""Shared helper utilities and constants for supply chain optimizer."""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Optional

# --- Seasonal transit day lookup ---
# Normal season: April-November (+0), Winter: December-March (+1 day)
WINTER_MONTHS = {12, 1, 2, 3}

# Default destination transit days (normal season)
DESTINATION_CODES = {
    "CC": "长春",
    "DL": "大连",
    "TJ": "天津",
}

LOCAL_DELIVERY_DAYS = 1.0

# --- Service level Z scores ---
SERVICE_LEVEL_Z = {
    0.90: 1.28,
    0.95: 1.65,
    0.99: 2.33,
}

SERVICE_LEVEL_Z_LOOKUP = {1.28: 0.90, 1.65: 0.95, 2.33: 0.99}


def is_winter(dt: Optional[datetime] = None) -> bool:
    """Return True if the given date is in winter months (Dec-Mar)."""
    if dt is None:
        dt = datetime.now()
    return dt.month in WINTER_MONTHS


def get_transit_days(dest_code: str, dt: Optional[datetime] = None) -> int:
    """Get transit days for a destination, +1 in winter."""
    base = {"CC": 4, "DL": 3, "TJ": 2}
    days = base.get(dest_code, 4)
    if is_winter(dt):
        days += 1
    return days


def get_local_delivery_days() -> float:
    return LOCAL_DELIVERY_DAYS


def calc_preposition_days(transit_days: int, x: int, local_delivery: float = LOCAL_DELIVERY_DAYS) -> float:
    """Preposition lead days = transit_days - (x - local_delivery). Positive means preposition needed."""
    return transit_days - (x - local_delivery)


def calc_safety_stock(z: float, sigma: float, L: float) -> float:
    """Safety stock = Z * sigma * sqrt(L)."""
    return z * sigma * math.sqrt(L)


def fmt_rmb(amount: float) -> str:
    return f"¥{amount:,.2f}"


def fmt_pct(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def now_shanghai() -> datetime:
    """Return current time (placeholder for Asia/Shanghai timezone)."""
    return datetime.now()
