"""Command line: ``eecalc <command> ...``. Values accept SI prefixes (4k7, 100n)."""

from __future__ import annotations

import argparse
import sys

from . import circuits, eseries, pcb
from .units import fmt, parse


def _num(s: str) -> float:
    try:
        return parse(s)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None


def _cmd_trace(a):
    w = pcb.trace_width(a.current, a.rise, a.oz, a.layer)
    print(f"Trace width: {w}")
    print(f"  ({a.current} A, {a.rise} °C rise, {a.oz} oz copper, IPC-2221)")


def _cmd_nearest(a):
    v = eseries.nearest(a.value, a.series)
    err = (v - a.value) / a.value * 100
    print(f"{fmt(v)} ({a.series}, {err:+.2f}% from {fmt(a.value)})")


def _cmd_divider(a):
    p = eseries.divider_pair(a.vout / a.vin, a.series, a.rmin, a.rmax)
    print(f"R_top = {fmt(p.r_top, 'Ω')}, R_bottom = {fmt(p.r_bottom, 'Ω')}")
    print(f"Vout = {a.vin * p.ratio:.4g} V ({p.error_pct:+.2f}%)")
    print(f"Divider current = {fmt(a.vin / (p.r_top + p.r_bottom), 'A')}")


def _cmd_led(a):
    r = circuits.led_resistor(a.supply, a.vf, a.current, a.count, a.series)
    print(f"Resistor: {fmt(r.standard_ohms, 'Ω')} (exact {fmt(r.exact_ohms, 'Ω')})")
    print(f"LED current: {fmt(r.actual_current_a, 'A')}")
    print(f"Resistor power: {fmt(r.resistor_power_w, 'W')} -> use a {r.suggested_rating_w:g} W part")


def _cmd_rc(a):
    if a.f:
        pick = circuits.rc_for_cutoff(a.f, a.c)
        print(f"R = {fmt(pick.r, 'Ω')}, C = {fmt(pick.c, 'F')}")
        print(f"fc = {fmt(pick.cutoff_hz, 'Hz')} ({pick.error_pct:+.2f}%)")
    elif a.r and a.c:
        print(f"fc = {fmt(circuits.rc_cutoff(a.r, a.c), 'Hz')}")
        print(f"tau = {fmt(circuits.time_constant(a.r, a.c), 's')}")
    else:
        sys.exit("give -r and -c, or -f (and optionally -c)")


def _cmd_lc(a):
    print(f"f0 = {fmt(circuits.lc_resonance(a.l, a.c), 'Hz')}")


def _cmd_microstrip(a):
    z = pcb.microstrip_impedance(a.width, a.height, a.er, a.oz)
    print(f"Z0 = {z:.1f} Ω  (IPC-2141 approximation)")


def _cmd_parallel(a):
    print(fmt(circuits.parallel(*a.values)))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eecalc", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("trace", help="PCB trace width for a current (IPC-2221)")
    s.add_argument("current", type=_num, help="current in A")
    s.add_argument("--rise", type=_num, default=10.0, help="temp rise °C (default 10)")
    s.add_argument("--oz", type=_num, default=1.0, help="copper weight oz (default 1)")
    s.add_argument("--layer", default="external", choices=["external", "internal"])
    s.set_defaults(func=_cmd_trace)

    s = sub.add_parser("nearest", help="nearest standard E-series value")
    s.add_argument("value", type=_num)
    s.add_argument("--series", default="E24")
    s.set_defaults(func=_cmd_nearest)

    s = sub.add_parser("divider", help="pick standard resistors for a voltage divider")
    s.add_argument("vin", type=_num)
    s.add_argument("vout", type=_num)
    s.add_argument("--series", default="E24")
    s.add_argument("--rmin", type=_num, default=1e3)
    s.add_argument("--rmax", type=_num, default=100e3)
    s.set_defaults(func=_cmd_divider)

    s = sub.add_parser("led", help="LED series resistor")
    s.add_argument("supply", type=_num, help="supply voltage")
    s.add_argument("vf", type=_num, help="LED forward voltage")
    s.add_argument("--current", type=_num, default=0.02, help="LED current A (default 20m)")
    s.add_argument("--count", type=int, default=1, help="LEDs in series")
    s.add_argument("--series", default="E24")
    s.set_defaults(func=_cmd_led)

    s = sub.add_parser("rc", help="RC filter cutoff, or pick R/C for a cutoff")
    s.add_argument("-r", type=_num)
    s.add_argument("-c", type=_num)
    s.add_argument("-f", type=_num, help="target cutoff Hz")
    s.set_defaults(func=_cmd_rc)

    s = sub.add_parser("lc", help="LC resonant frequency")
    s.add_argument("l", type=_num)
    s.add_argument("c", type=_num)
    s.set_defaults(func=_cmd_lc)

    s = sub.add_parser("microstrip", help="microstrip impedance")
    s.add_argument("width", type=_num, help="trace width mm")
    s.add_argument("height", type=_num, help="dielectric height mm")
    s.add_argument("--er", type=_num, default=4.4)
    s.add_argument("--oz", type=_num, default=1.0)
    s.set_defaults(func=_cmd_microstrip)

    s = sub.add_parser("parallel", help="resistors in parallel")
    s.add_argument("values", type=_num, nargs="+")
    s.set_defaults(func=_cmd_parallel)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
