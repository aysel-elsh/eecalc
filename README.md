# eecalc

**The electronics calculations you keep Googling, as one small Python library and CLI.**

No dependencies. Every formula cites its source and is tested against reference values.

```bash
pip install git+https://github.com/aysel-elsh/eecalc
```

## CLI

Values take SI prefixes and RKM codes: `4.7k`, `4k7`, `100n`, `2M2`, `4R7`.

```console
$ eecalc trace 3 --oz 2                 # PCB trace width for 3 A
Trace width: 0.684 mm (26.9 mil), external layer

$ eecalc divider 5 3.3                  # standard resistors for 5 V -> 3.3 V
R_top = 47 kΩ, R_bottom = 91 kΩ
Vout = 3.297 V (-0.09%)

$ eecalc led 12 3.1 --count 3           # 3 white LEDs on 12 V
Resistor: 150 Ω (exact 135 Ω)
LED current: 18 mA
Resistor power: 48.6 mW -> use a 0.1 W part

$ eecalc rc -f 1k                       # pick R and C for a 1 kHz low-pass
R = 16 kΩ, C = 10 nF
fc = 995 Hz (-0.53%)

$ eecalc nearest 14.2k --series E96
14.3 k (E96, +0.70% from 14.2 k)
```

Other commands: `lc`, `microstrip`, `parallel`. Run `eecalc <command> -h` for options.

## Python

```python
import eecalc as ee

ee.trace_width(2.0, temp_rise_c=10, copper_oz=1, layer="external")  # TraceWidth(width_mm=0.78, ...)
ee.trace_current(width_mm=0.5)                    # amps a 0.5 mm trace can carry
ee.trace_resistance(width_mm=0.25, length_mm=100) # Ω
ee.microstrip_impedance(0.3, 0.2, er=4.4)         # ≈ 53 Ω

ee.nearest(4600, "E12")                           # 4700.0
ee.values("E24", 1e3, 10e3)                       # every E24 value from 1k to 10k
ee.divider_pair(3.3 / 5)                          # best E24 pair for a ratio

ee.led_resistor(5, led_vf=2.0, led_current_a=0.02)
ee.rc_cutoff(10e3, 100e-9)                        # Hz
ee.rc_for_cutoff(1000)                            # standard R + C for 1 kHz
ee.lc_resonance(10e-6, 100e-9)
ee.parallel(4.7e3, 4.7e3)
ee.power(v=12, r=6)                               # {'v': 12, 'i': 2.0, 'r': 6, 'p': 24.0}

ee.parse("4k7"), ee.fmt(4700, "Ω")                # 4700.0, '4.7 kΩ'
```

## What's inside

| Area | Functions | Source |
|---|---|---|
| PCB | `trace_width`, `trace_current`, `trace_resistance`, `microstrip_impedance` | IPC-2221, IPC-2141 |
| Standard values | `nearest`, `values`, `divider_pair`, `SERIES` (E3–E192) | IEC 60063 |
| Circuits | `led_resistor`, `rc_cutoff`, `rl_cutoff`, `rc_for_cutoff`, `lc_resonance`, `reactance_c`, `reactance_l`, `time_constant`, `divider_vout`, `series`, `parallel`, `power` | textbook |
| Units | `parse`, `fmt` | SI / IEC 60062 RKM |

**Notes on accuracy.** IPC-2221 is the conservative curve most online calculators use; it is
not IPC-2152. The microstrip formula is good to a few percent for 0.1 < w/h < 2. Copper is
taken as 35 µm (1.378 mil) per oz, the same value those calculators use.

## Use it from an AI assistant

[eecalc-mcp](https://github.com/aysel-elsh/eecalc-mcp) exposes these functions as an MCP
server, so Claude, Cursor and similar tools compute exact answers instead of guessing at the math.

## Contributing

New calculators are welcome (good first issues: stripline impedance, IPC-2152, via
current, op-amp gain, 555 timer, battery life). Each one needs a docstring with the
formula's source and a test against a published reference value.

```bash
pip install -e . pytest && pytest
```

MIT License.
