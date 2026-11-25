"""IEC 60063 preferred-number series (E6 ... E192) and helpers to snap to them."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import product

__all__ = ["SERIES", "values", "nearest", "divider_pair", "DividerPair"]

# The E3-E24 values are historical and don't follow the formula, so list them.
_E24 = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1,
]
_E192 = [
    1.00, 1.01, 1.02, 1.04, 1.05, 1.06, 1.07, 1.09, 1.10, 1.11, 1.13, 1.14,
    1.15, 1.17, 1.18, 1.20, 1.21, 1.23, 1.24, 1.26, 1.27, 1.29, 1.30, 1.32,
    1.33, 1.35, 1.37, 1.38, 1.40, 1.42, 1.43, 1.45, 1.47, 1.49, 1.50, 1.52,
    1.54, 1.56, 1.58, 1.60, 1.62, 1.64, 1.65, 1.67, 1.69, 1.72, 1.74, 1.76,
    1.78, 1.80, 1.82, 1.84, 1.87, 1.89, 1.91, 1.93, 1.96, 1.98, 2.00, 2.03,
    2.05, 2.08, 2.10, 2.13, 2.15, 2.18, 2.21, 2.23, 2.26, 2.29, 2.32, 2.34,
    2.37, 2.40, 2.43, 2.46, 2.49, 2.52, 2.55, 2.58, 2.61, 2.64, 2.67, 2.71,
    2.74, 2.77, 2.80, 2.84, 2.87, 2.91, 2.94, 2.98, 3.01, 3.05, 3.09, 3.12,
    3.16, 3.20, 3.24, 3.28, 3.32, 3.36, 3.40, 3.44, 3.48, 3.52, 3.57, 3.61,
    3.65, 3.70, 3.74, 3.79, 3.83, 3.88, 3.92, 3.97, 4.02, 4.07, 4.12, 4.17,
    4.22, 4.27, 4.32, 4.37, 4.42, 4.48, 4.53, 4.59, 4.64, 4.70, 4.75, 4.81,
    4.87, 4.93, 4.99, 5.05, 5.11, 5.17, 5.23, 5.30, 5.36, 5.42, 5.49, 5.56,
    5.62, 5.69, 5.76, 5.83, 5.90, 5.97, 6.04, 6.12, 6.19, 6.26, 6.34, 6.42,
    6.49, 6.57, 6.65, 6.73, 6.81, 6.90, 6.98, 7.06, 7.15, 7.23, 7.32, 7.41,
    7.50, 7.59, 7.68, 7.77, 7.87, 7.96, 8.06, 8.16, 8.25, 8.35, 8.45, 8.56,
    8.66, 8.76, 8.87, 8.98, 9.09, 9.20, 9.31, 9.42, 9.53, 9.65, 9.76, 9.88,
]

SERIES: dict[str, list[float]] = {
    "E3": _E24[::8],
    "E6": _E24[::4],
    "E12": _E24[::2],
    "E24": _E24,
    "E48": _E192[::4],
    "E96": _E192[::2],
    "E192": _E192,
}


def _base(series: str) -> list[float]:
    key = series.upper()
    if key not in SERIES:
        raise ValueError(f"unknown series {series!r}; pick one of {', '.join(SERIES)}")
    return SERIES[key]


def values(series: str = "E24", lo: float = 1.0, hi: float = 1e7) -> list[float]:
    """All values of a series between ``lo`` and ``hi`` (inclusive)."""
    base = _base(series)
    out = []
    for decade in range(math.floor(math.log10(lo)) - 1, math.ceil(math.log10(hi)) + 1):
        for b in base:
            v = round(b * 10**decade, 12)
            if lo * (1 - 1e-9) <= v <= hi * (1 + 1e-9):
                out.append(v)
    return sorted(set(out))


def nearest(value: float, series: str = "E24") -> float:
    """Closest standard value (by ratio, not absolute difference).

    >>> nearest(4600, "E12")
    4700.0
    """
    if value <= 0:
        raise ValueError("value must be positive")
    base = _base(series)
    decade = math.floor(math.log10(value))
    candidates = [b * 10 ** (decade + d) for d in (-1, 0, 1) for b in base]
    best = min(candidates, key=lambda c: abs(math.log(c / value)))
    return round(best, 12)


@dataclass(frozen=True)
class DividerPair:
    r_top: float
    r_bottom: float
    ratio: float  # Vout / Vin actually achieved
    error_pct: float


def divider_pair(
    target_ratio: float,
    series: str = "E24",
    r_min: float = 1e3,
    r_max: float = 100e3,
) -> DividerPair:
    """Best pair of standard resistors for ``Vout/Vin = Rb / (Rt + Rb)``.

    Searches every pair between ``r_min`` and ``r_max`` (default 1k-100k,
    a sensible range for most logic-level dividers).

    >>> p = divider_pair(3.3 / 5.0, "E24")
    >>> abs(p.error_pct) < 0.5
    True
    """
    if not 0 < target_ratio < 1:
        raise ValueError("target_ratio must be between 0 and 1")
    vals = values(series, r_min, r_max)
    best = None
    for rt, rb in product(vals, vals):
        ratio = rb / (rt + rb)
        err = abs(ratio - target_ratio)
        # tie-break toward higher total resistance (less wasted current)
        key = (round(err, 12), -(rt + rb))
        if best is None or key < best[0]:
            best = (key, rt, rb, ratio)
    _, rt, rb, ratio = best
    return DividerPair(rt, rb, ratio, (ratio - target_ratio) / target_ratio * 100)
