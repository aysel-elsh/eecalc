"""Parse and format values with SI prefixes ("4.7k", "100nF", "2M2")."""

from __future__ import annotations

import math
import re

__all__ = ["parse", "fmt"]

_PREFIX = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "µ": 1e-6,
    "μ": 1e-6,
    "m": 1e-3,
    "": 1.0,
    "k": 1e3,
    "K": 1e3,
    "M": 1e6,
    "G": 1e9,
    "T": 1e12,
}

# Units we strip off the end. "R" doubles as a decimal marker ("4R7" = 4.7).
_UNITS = ("ohms", "ohm", "Ω", "F", "H", "V", "A", "W", "Hz", "s")

_NUM = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*([fpnuµμmkKMGT]?)$")
# RKM code: 4k7, 2M2, 4R7, 0R1
_RKM = re.compile(r"^(\d*)([RkKMGmunp])(\d+)$")


def parse(value: str | float | int) -> float:
    """Turn ``"4.7k"``, ``"4k7"``, ``"100nF"``, ``"10 uH"`` or ``2.2e3`` into a float.

    >>> parse("4k7")
    4700.0
    >>> parse("2M2")
    2200000.0
    """
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "")
    if not s:
        raise ValueError("empty value")
    for unit in sorted(_UNITS, key=len, reverse=True):
        if s.endswith(unit) and len(s) > len(unit):
            s = s[: -len(unit)]
            break
    m = _NUM.match(s)
    if m:
        return float(m.group(1)) * _PREFIX[m.group(2)]
    m = _RKM.match(s)
    if m:
        whole, letter, frac = m.groups()
        mult = 1.0 if letter == "R" else _PREFIX[letter]
        return float(f"{whole or '0'}.{frac}") * mult
    raise ValueError(f"can't parse {value!r} as a number")


_FMT_PREFIX = [
    (1e12, "T"),
    (1e9, "G"),
    (1e6, "M"),
    (1e3, "k"),
    (1.0, ""),
    (1e-3, "m"),
    (1e-6, "u"),
    (1e-9, "n"),
    (1e-12, "p"),
    (1e-15, "f"),
]


def fmt(value: float, unit: str = "", digits: int = 3) -> str:
    """Format a number with an SI prefix: ``fmt(4700, "Ω") -> "4.7 kΩ"``."""
    if value == 0 or not math.isfinite(value):
        return f"{value:g} {unit}".strip()
    a = abs(value)
    for mult, p in _FMT_PREFIX:
        if a >= mult * 0.9995:
            break
    scaled = value / mult
    return f"{scaled:.{digits}g} {p}{unit}".strip()
