"""Everyday circuit math: dividers, RC/LC filters, LED resistors, reactance."""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import eseries

__all__ = [
    "series",
    "parallel",
    "divider_vout",
    "rc_cutoff",
    "rl_cutoff",
    "lc_resonance",
    "rc_for_cutoff",
    "reactance_c",
    "reactance_l",
    "time_constant",
    "LedResistor",
    "led_resistor",
    "power",
]


def series(*values: float) -> float:
    """Resistors (or inductors) in series."""
    if not values:
        raise ValueError("give at least one value")
    return float(sum(values))


def parallel(*values: float) -> float:
    """Resistors (or inductors) in parallel. Also: capacitors in series."""
    if not values:
        raise ValueError("give at least one value")
    if any(v <= 0 for v in values):
        raise ValueError("values must be positive")
    return 1.0 / sum(1.0 / v for v in values)


def divider_vout(vin: float, r_top: float, r_bottom: float, r_load: float | None = None) -> float:
    """Output of a resistor divider, optionally with a load on the output."""
    rb = parallel(r_bottom, r_load) if r_load else r_bottom
    return vin * rb / (r_top + rb)


def rc_cutoff(r: float, c: float) -> float:
    """-3 dB frequency (Hz) of a first-order RC filter: 1 / (2πRC)."""
    if r <= 0 or c <= 0:
        raise ValueError("R and C must be positive")
    return 1.0 / (2 * math.pi * r * c)


def rl_cutoff(r: float, l: float) -> float:
    """-3 dB frequency (Hz) of a first-order RL filter: R / (2πL)."""
    if r <= 0 or l <= 0:
        raise ValueError("R and L must be positive")
    return r / (2 * math.pi * l)


def lc_resonance(l: float, c: float) -> float:
    """Resonant frequency (Hz) of an LC tank: 1 / (2π√(LC))."""
    if l <= 0 or c <= 0:
        raise ValueError("L and C must be positive")
    return 1.0 / (2 * math.pi * math.sqrt(l * c))


@dataclass(frozen=True)
class RCPick:
    r: float
    c: float
    cutoff_hz: float
    error_pct: float


def rc_for_cutoff(
    f_hz: float,
    c: float | None = None,
    r_series: str = "E24",
    c_series: str = "E12",
) -> RCPick:
    """Pick standard R (and C) values for a target cutoff frequency.

    If ``c`` is given, only R is chosen. Otherwise every E12 capacitor from
    100 pF to 10 µF is tried, keeping R between 1 kΩ and 1 MΩ.
    """
    if f_hz <= 0:
        raise ValueError("frequency must be positive")
    caps = [c] if c else eseries.values(c_series, 100e-12, 10e-6)
    best = None
    for cap in caps:
        r_ideal = 1 / (2 * math.pi * f_hz * cap)
        if not c and not 1e3 <= r_ideal <= 1e6:
            continue
        r = eseries.nearest(r_ideal, r_series)
        fc = rc_cutoff(r, cap)
        err = (fc - f_hz) / f_hz * 100
        if best is None or abs(err) < abs(best.error_pct):
            best = RCPick(r, cap, fc, err)
    if best is None:
        raise ValueError("no R/C combination found in range; pass c explicitly")
    return best


def reactance_c(f_hz: float, c: float) -> float:
    """Capacitive reactance in ohms: 1 / (2πfC)."""
    return 1.0 / (2 * math.pi * f_hz * c)


def reactance_l(f_hz: float, l: float) -> float:
    """Inductive reactance in ohms: 2πfL."""
    return 2 * math.pi * f_hz * l


def time_constant(r: float, c: float) -> float:
    """RC time constant τ in seconds. The cap reaches ~63% in τ, ~99% in 5τ."""
    return r * c


@dataclass(frozen=True)
class LedResistor:
    exact_ohms: float
    standard_ohms: float
    actual_current_a: float
    resistor_power_w: float
    suggested_rating_w: float


_RATINGS = [0.0625, 0.1, 0.125, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0]


def led_resistor(
    supply_v: float,
    led_vf: float,
    led_current_a: float = 0.02,
    n_leds: int = 1,
    series: str = "E24",
) -> LedResistor:
    """Series resistor for one or more LEDs in a string.

    Rounds *up* to the next standard value so the LED never gets more current
    than asked for. The power rating has 2x margin.
    """
    headroom = supply_v - led_vf * n_leds
    if headroom <= 0:
        raise ValueError(
            f"supply ({supply_v} V) must be higher than total LED drop ({led_vf * n_leds} V)"
        )
    if led_current_a <= 0:
        raise ValueError("LED current must be positive")
    exact = headroom / led_current_a
    std = next(v for v in eseries.values(series, exact * 0.999, exact * 20) if v >= exact * 0.999)
    i = headroom / std
    p = i * i * std
    rating = next((r for r in _RATINGS if r >= 2 * p), _RATINGS[-1])
    return LedResistor(exact, std, i, p, rating)


def power(v: float | None = None, i: float | None = None, r: float | None = None) -> dict:
    """Ohm's law + power: give any two of V, I, R and get all four quantities."""
    given = sum(x is not None for x in (v, i, r))
    if given != 2:
        raise ValueError("give exactly two of v, i, r")
    if v is None:
        v = i * r
    elif i is None:
        i = v / r
    else:
        r = v / i
    return {"v": v, "i": i, "r": r, "p": v * i}
