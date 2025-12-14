"""Normalisation/cleaning des données produits/shops."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def normalize_price(value: Optional[str | float | int]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    txt = value.replace("\xa0", " ").replace(",", ".")
    matches = re.findall(r"[\d\.]+", txt)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except Exception:
        return None


def normalize_reviews(value: Optional[str | int]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = re.findall(r"\d+", value.replace(",", ""))
    return int(digits[0]) if digits else None


def to_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).isoformat()
    except Exception:
        return None



from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def normalize_price(value: Optional[str | float | int]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    txt = value.replace("\xa0", " ").replace(",", ".")
    matches = re.findall(r"[\d\.]+", txt)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except Exception:
        return None


def normalize_reviews(value: Optional[str | int]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = re.findall(r"\d+", value.replace(",", ""))
    return int(digits[0]) if digits else None


def to_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).isoformat()
    except Exception:
        return None


