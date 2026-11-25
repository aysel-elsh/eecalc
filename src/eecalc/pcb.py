"""PCB calculations: IPC-2221 trace width, trace resistance, microstrip impedance.

Units: millimetres, amps, °C, ounces of copper. 1 oz/ft² copper is taken as 35 µm (1.378 mil) thick.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "OZ_TO_MM",
    "TraceWidth",
    "trace_width",
    "trace_current",
    "trace_resistance",
    "microstrip_impedance",
]

OZ_TO_MM = 0.035  # 1 oz copper ≈ 35 µm (1.378 mil), the value IPC calculators use
_MIL = 0.0254  # mm per mil
_RHO_CU = 1.724e-8  # Ω·m at 20 °C
_ALPHA_CU = 0.00393  # 1/°C

# IPC-2221 constants: I = k * dT^0.44 * A^0.725, A in mil²
_K = {"external": 0.048, "internal": 0.024}


@dataclass(frozen=True)
class TraceWidth:
    width_mm: float
    width_mil: float
    area_mil2: float
    layer: str

    def __str__(self) -> str:
        return f"{self.width_mm:.3f} mm ({self.width_mil:.1f} mil), {self.layer} layer"


def _check_layer(layer: str) -> str:
    layer = layer.lower()
    if layer not in _K:
        raise ValueError("layer must be 'external' or 'internal'")
    return layer


def trace_width(
    current_a: float,
    temp_rise_c: float = 10.0,
    copper_oz: float = 1.0,
    layer: str = "external",
) -> TraceWidth:
    """Minimum trace width for a current, per IPC-2221.

    IPC-2221 is the classic, conservative chart fit. It's fine for most boards;
    use IPC-2152 data if you're pushing current hard.

    >>> round(trace_width(1.0, 10, 1.0).width_mil, 1)
    11.8
    """
    if current_a <= 0 or temp_rise_c <= 0 or copper_oz <= 0:
        raise ValueError("current, temperature rise and copper weight must be positive")
    layer = _check_layer(layer)
    area = (current_a / (_K[layer] * temp_rise_c**0.44)) ** (1 / 0.725)
    thickness_mil = copper_oz * OZ_TO_MM / _MIL
    w_mil = area / thickness_mil
    return TraceWidth(w_mil * _MIL, w_mil, area, layer)


def trace_current(
    width_mm: float,
    temp_rise_c: float = 10.0,
    copper_oz: float = 1.0,
    layer: str = "external",
) -> float:
    """Max current (A) a trace can carry for a given temperature rise (IPC-2221)."""
    if width_mm <= 0 or temp_rise_c <= 0 or copper_oz <= 0:
        raise ValueError("width, temperature rise and copper weight must be positive")
    layer = _check_layer(layer)
    area = (width_mm / _MIL) * (copper_oz * OZ_TO_MM / _MIL)
    return _K[layer] * temp_rise_c**0.44 * area**0.725


def trace_resistance(
    width_mm: float,
    length_mm: float,
    copper_oz: float = 1.0,
    temp_c: float = 25.0,
) -> float:
    """DC resistance of a copper trace in ohms."""
    if width_mm <= 0 or length_mm <= 0 or copper_oz <= 0:
        raise ValueError("width, length and copper weight must be positive")
    area_m2 = (width_mm * 1e-3) * (copper_oz * OZ_TO_MM * 1e-3)
    rho = _RHO_CU * (1 + _ALPHA_CU * (temp_c - 20.0))
    return rho * (length_mm * 1e-3) / area_m2


def microstrip_impedance(
    width_mm: float,
    height_mm: float,
    er: float = 4.4,
    copper_oz: float = 1.0,
) -> float:
    """Characteristic impedance (Ω) of a surface microstrip, IPC-2141 formula.

    ``height_mm`` is the dielectric thickness to the reference plane. ``er`` is
    the dielectric constant (FR-4 is about 4.2-4.6). The formula is accurate to
    a few percent for 0.1 < w/h < 2.0 and 1 < er < 15.

    >>> round(microstrip_impedance(0.3, 0.2, 4.4), 1)
    53.1
    """
    if width_mm <= 0 or height_mm <= 0 or er < 1:
        raise ValueError("width and height must be positive and er >= 1")
    t = copper_oz * OZ_TO_MM
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * height_mm / (0.8 * width_mm + t))
