import math

import pytest

import eecalc as ee
from eecalc.cli import main


# --- units ----------------------------------------------------------------
@pytest.mark.parametrize(
    "s, expected",
    [
        ("4.7k", 4700),
        ("4k7", 4700),
        ("2M2", 2.2e6),
        ("4R7", 4.7),
        ("0R1", 0.1),
        ("100nF", 100e-9),
        ("10 uH", 10e-6),
        ("10µF", 10e-6),
        ("1e3", 1000),
        ("3.3V", 3.3),
        ("50ohm", 50),
        (220, 220),
    ],
)
def test_parse(s, expected):
    assert ee.parse(s) == pytest.approx(expected)


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        ee.parse("banana")


def test_fmt():
    assert ee.fmt(4700, "Ω") == "4.7 kΩ"
    assert ee.fmt(1e-7, "F") == "100 nF"
    assert ee.fmt(0.5, "W") == "500 mW"


# --- E-series -------------------------------------------------------------
def test_series_lengths():
    for name, n in [("E3", 3), ("E6", 6), ("E12", 12), ("E24", 24), ("E48", 48), ("E96", 96), ("E192", 192)]:
        assert len(ee.SERIES[name]) == n


@pytest.mark.parametrize(
    "value, series, expected",
    [(4600, "E12", 4700), (1000, "E24", 1000), (9900, "E12", 10000), (5.0, "E96", 4.99), (14.2e3, "E96", 14.3e3)],
)
def test_nearest(value, series, expected):
    assert ee.nearest(value, series) == pytest.approx(expected)


def test_divider_pair_5v_to_3v3():
    p = ee.divider_pair(3.3 / 5, "E24")
    assert abs(p.error_pct) < 0.5
    assert p.r_bottom / (p.r_top + p.r_bottom) == pytest.approx(p.ratio)


# --- PCB ------------------------------------------------------------------
def test_trace_width_matches_ipc2221_reference():
    # Well-known reference point: 1 A, 10 °C, 1 oz outer ~ 11.8 mil (0.30 mm)
    w = ee.trace_width(1.0, 10, 1.0, "external")
    assert w.width_mil == pytest.approx(11.8, abs=0.1)
    # internal layers need ~2.6x the width for the same current
    wi = ee.trace_width(1.0, 10, 1.0, "internal")
    assert wi.width_mil / w.width_mil == pytest.approx(2 ** (1 / 0.725), rel=1e-6)


def test_trace_current_is_inverse_of_width():
    w = ee.trace_width(3.0, 20, 2.0)
    assert ee.trace_current(w.width_mm, 20, 2.0) == pytest.approx(3.0)


def test_trace_resistance():
    # 0.254 mm (10 mil) x 1 oz x 1 m ~ 1.95 Ω at 20 °C
    r = ee.trace_resistance(0.254, 1000, 1.0, temp_c=20)
    assert r == pytest.approx(1.95, rel=0.01)


def test_microstrip_50ohm_ballpark():
    z = ee.microstrip_impedance(0.3, 0.2, 4.4)
    assert 45 < z < 60


# --- circuits -------------------------------------------------------------
def test_parallel_series():
    assert ee.parallel(1000, 1000) == pytest.approx(500)
    assert ee.series(1, 2, 3) == 6


def test_divider_vout_with_load():
    assert ee.divider_vout(10, 10e3, 10e3) == pytest.approx(5)
    assert ee.divider_vout(10, 10e3, 10e3, r_load=10e3) == pytest.approx(10 / 3)


def test_rc_cutoff():
    assert ee.rc_cutoff(1e3, 159.155e-9) == pytest.approx(1000, rel=1e-4)


def test_rc_for_cutoff_hits_target():
    pick = ee.rc_for_cutoff(1000)
    assert abs(pick.error_pct) < 3


def test_lc_resonance():
    assert ee.lc_resonance(10e-6, 100e-9) == pytest.approx(1 / (2 * math.pi * math.sqrt(1e-12)))


def test_led_resistor_rounds_up():
    r = ee.led_resistor(5, 2.0, 0.02)
    assert r.exact_ohms == pytest.approx(150)
    assert r.standard_ohms == pytest.approx(150)
    r = ee.led_resistor(12, 3.1, 0.02, n_leds=3)  # 140 Ω exact
    assert r.standard_ohms >= r.exact_ohms
    assert r.actual_current_a <= 0.02


def test_led_resistor_bad_supply():
    with pytest.raises(ValueError):
        ee.led_resistor(3.3, 3.2, 0.02, n_leds=2)


def test_power():
    assert ee.power(v=12, r=6) == {"v": 12, "i": 2, "r": 6, "p": 24}


# --- CLI ------------------------------------------------------------------
def test_cli_trace(capsys):
    main(["trace", "1"])
    assert "0.300 mm" in capsys.readouterr().out


def test_cli_accepts_si_prefixes(capsys):
    main(["parallel", "4k7", "4k7"])
    assert capsys.readouterr().out.strip() == "2.35 k"
