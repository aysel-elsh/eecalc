"""eecalc: the electronics calculations you keep Googling, as a Python library.

Example::

    import eecalc as ee
    ee.trace_width(2.0).width_mm      # IPC-2221, 10 °C rise, 1 oz, outer layer
    ee.nearest(4600, "E12")           # 4700.0
    ee.led_resistor(5, 2.0, 0.02)     # 150 Ω, 1/8 W is enough
"""

from .circuits import (
    divider_vout,
    lc_resonance,
    led_resistor,
    parallel,
    power,
    rc_cutoff,
    rc_for_cutoff,
    reactance_c,
    reactance_l,
    rl_cutoff,
    series,
    time_constant,
)
from .eseries import SERIES, divider_pair, nearest, values
from .pcb import microstrip_impedance, trace_current, trace_resistance, trace_width
from .units import fmt, parse

__version__ = "0.1.0"

__all__ = [
    "SERIES",
    "divider_pair",
    "divider_vout",
    "fmt",
    "lc_resonance",
    "led_resistor",
    "microstrip_impedance",
    "nearest",
    "parallel",
    "parse",
    "power",
    "rc_cutoff",
    "rc_for_cutoff",
    "reactance_c",
    "reactance_l",
    "rl_cutoff",
    "series",
    "time_constant",
    "trace_current",
    "trace_resistance",
    "trace_width",
    "values",
]
