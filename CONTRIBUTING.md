# Contributing to partinfo

partinfo is a curated, datasheet-verified component reference. The value is
trust: an entry is only worth having if its data is correct and its provenance
is clear. These notes are the bar an entry has to meet.

## Adding or editing a part

Parts are one JSON file each under `src/partinfo/data/parts/<category>/`, validated against the
Pydantic schema in `src/partinfo/schema.py`. After any change, rebuild the
index:

```sh
partinfo ingest
```

Directory names are cosmetic; the `category` field is what matters. Before a
new entry, check for an id collision:

```sh
find src/partinfo/data/parts -name '*.json' -exec basename {} \; | sort | uniq -d
```

## Provenance rules (non-negotiable)

- **Verify against the primary manufacturer datasheet.** Never an aggregator
  (alldatasheet, datasheetspdf, lcsc, octopart). Cite the primary PDF in
  `datasheet_url`.
- **Position first, names second.** Confirm which physical pin number is which
  function by reading the actual package drawing. A pinout is right or wrong at
  the pin-number level; labels are cosmetic on top of that.
- **`verified: true` means a human or agent read the primary datasheet and
  checked the pins against it.** Not "cross-checked from memory," not "an
  aggregator agreed." If you could not reach a primary sheet, leave it `false`
  and say why. An honest `false` beats a hopeful `true`.
- **`datasheet_name`** (per pin): the verbatim vendor label, set only when it
  differs from the normalized house `name` (e.g. house `Q0` vs TI `QA`). The
  same die ships under different vendor labels; this records that without
  losing cross-part consistency.
- **`variants`**: when a generic number ships from different vendors with
  genuinely different physical pinouts (e.g. 2N2222 onsemi C-B-E vs the common
  E-B-C), keep the common pinout on the part and add each divergent one as a
  variant with its own datasheet. Never let a variant hide a wrong pinout.
- **`human_reviewed`**: set this to `true` once a human has personally checked
  a non-human-sourced (`source: claude`/`ollama`) entry and confirms it's
  correct. This suppresses the "verify before trusting" warning. It does NOT
  change `source` -- that stays a permanent, honest record of who actually
  wrote the entry. Never set `human_reviewed` on an entry you haven't actually
  checked; it exists so verification can be recorded once, not skipped.

## Connectors and cables

Connectors (OBD-II, DB9, ...) are a separate content type from parts: JSON
under `src/partinfo/data/connectors/`, validated against `Connector` in
`schema.py`, served by the `conn` CLI namespace. Same provenance discipline as
parts:

- **Verify the pinout against the standard or a primary source.** Pin position
  is right or wrong; take it from the connector standard (SAE J1962,
  TIA/EIA-232, the device datasheet's connector drawing), not a random pinout
  blog. `verified: true` only when it's checked against the standard.
- **`contacts`** = one entry per pin: `pin`, `name` (signal), optional `signal`
  (the standard/role), and a `description`.
- **Renderer hints:** set `form` (`dsub`, `header`, `inline`) and `rows` (pin
  numbers by physical row, top to bottom) and the ascii face-view draws itself.
  For a connector the generic renderer can't handle, hand-draw an `ascii` field
  and it overrides the renderer.
- **`variants`** capture physical/protocol differences (OBD-II Type A vs B; a
  pin whose meaning changes by protocol). Cross-link `related` to the parts that
  drive the bus (a CAN connector -> mcp2515 / tja1050).

## Data completeness: store the inputs, not the datasheet

partinfo is a structured quick-reference and a source of **calculation
inputs**, sitting on top of datasheets. It is not a replacement for them.

The rule: **store the parameters that feed the calculations people actually run
for that device class.** Anything derivable from stored values plus a
`reference` entry (Ohm's law, the MOSFET formulas, RC time constants) does not
need to be stored, it is already covered. Anything unbounded or graphical (SOA
curves, full capacitance-vs-voltage plots, every temperature coefficient) does
not belong here; that is what `datasheet_url` is for.

The test for "complete": can a reader answer the common questions for this part
either from a stored field or by feeding stored fields into a reference
equation? If a common calculation needs an input we do not store, the entry is
incomplete, add the input.

### Core parameter sets by device class

A complete entry carries at least these. Put well-known typed values in the
`specs` fields and the rest in `specs.extra`.

Thermal resistance (`Rth(JC)`/`Rth(JA)`, referenced throughout the tables below)
has typed fields, `specs.rth_jc_cw`/`specs.rth_ja_cw`, alongside `extra`. This
is deliberately the only pair of parameters promoted out of `extra` so far --
universal across nearly every device class, and simple enough (always a bare
number for a given package/mounting) to type cleanly. When a datasheet gives
typ+max or several mounting conditions, the typed field holds the single most
conservative figure (max, or worst-case/no-heatsink); keep the full detail
with conditions in `extra` alongside it, don't drop it. Most other parameters
(Vce(sat), Qg, hFE ranges, etc.) stay in `extra` on purpose -- see the
argument against typing everything in the project history if you're
wondering why.

**MOSFET** (see `src/partinfo/data/parts/mosfet/irf520.json` for the reference example):

| group | parameters | feeds |
|-------|-----------|-------|
| ratings | V_DS, V_GS(max), I_D (cont. + pulsed), P_D | absolute limits |
| drive | V_GS(th), R_DS(on) *at its test V_GS*, logic-level y/n | turn-on, conduction loss |
| switching | Q_g, Q_gs, Q_gd, C_iss, C_oss, C_rss, t_d(on)/t_r/t_d(off)/t_f | gate drive, switching loss |
| thermal | R_th(JC), R_th(JA) | junction temperature, real current limit |
| body diode | V_SD, t_rr | flyback, reverse recovery |

Without the thermal and switching groups, the junction-temperature and
switching-loss calculations silently cannot be done, so those groups are part
of the bar, not optional extras.

**BJT** (bipolar transistor):

| group | parameters | feeds |
|-------|-----------|-------|
| ratings | V_CEO, V_CBO, V_EBO, I_C (cont. + peak), P_D | absolute limits |
| gain | h_FE range *at its test I_C* | base-current / drive calc |
| saturation | V_CE(sat), V_BE(on) | switch dissipation, base resistor |
| speed | f_T | small-signal / switching bandwidth |
| thermal (power BJT) | R_th(JC), R_th(JA) | junction temperature |

**Diode:**

| group | parameters | feeds |
|-------|-----------|-------|
| rectifier / signal | V_RRM, I_F(av), I_FSM, V_F *at its I_F*, I_R, t_rr | series resistor, loss, switching |
| zener | V_Z *at I_ZT*, P_Z, Z_ZT | zener bias resistor, regulation |
| thermal (power) | R_th | junction temperature |

**Regulator:**

| group | parameters | feeds |
|-------|-----------|-------|
| io | V_in(max), V_out (or adj range + V_ref), I_out(max) | headroom, divider |
| loss | dropout voltage, I_q (ground current) | dissipation, efficiency |
| thermal | R_th(JC), R_th(JA) | junction temperature, heatsink |

**Op-amp:**

| group | parameters | feeds |
|-------|-----------|-------|
| supply | V_s range, I_q | budgeting |
| ac | GBW, slew rate | bandwidth at gain |
| dc precision | V_os, I_bias, CMRR | offset / error |
| output | I_out (drive), input noise | load, noise budget |

**Germanium transistor** (`transistor_germanium`, see `src/partinfo/data/parts/germanium/ac128.json` for
the reference example):

| group | parameters | feeds |
|-------|-----------|-------|
| ratings | V_CBO, V_EBO, I_C (cont.), P_D | absolute limits |
| gain | h_FE range *at its test I_C* | base-current / drive calc, and see note below |
| saturation | V_CE(sat) or V_BE(sat) | switch dissipation |
| speed | f_T (or the nearest equivalent the datasheet actually reports) | switching bandwidth |
| thermal (power parts) | R_th(JC), R_th(JA) | junction temperature |
| leakage | I_CBO, I_EBO | germanium-specific: leakage is orders of magnitude worse than silicon and drives real dissipation and drift; store it even though silicon entries elsewhere in this repo mostly don't bother |

Note on h_FE: germanium parts from the 1960s commonly have a wider min-max
spread than any silicon part in this repo (a factor of 3 or more is normal),
and real units vary further with age and handling. Store the datasheet range
as given, don't average it into a single number.

Note on sourcing: many of these parts' original manufacturers (Newmarket
Transistors, and others) have been defunct for decades with no successor
maintaining documentation. A period catalog scan reached only through an
aggregator mirror is sometimes the best available source for electrical
characteristics; that's still better than nothing but is not a primary
citation; say so plainly in the entry and lean toward `verified: false` if
the pinout itself isn't confirmed by an actual manufacturer package drawing
(as opposed to the electrical specs, which can be reasonably cited from a
secondary compilation if cross-checked). Getting a physical pin position
wrong is worse than an honest gap; see the `db107` bridge-rectifier entry
for how much cross-referencing a position claim can take when the case
style isn't self-evident.

**JFET** (`transistor_jfet`, see `src/partinfo/data/parts/jfet/2n5457.json`):

| group | parameters | feeds |
|-------|-----------|-------|
| ratings | V_DS(max), V_GS(max), P_D | absolute limits |
| bias | V_GS(off), I_DSS *(both as ranges, not single numbers)* | self-bias resistor calc |
| gain | g_fs (forward transconductance) | stage gain estimate |
| thermal (power parts) | R_th(JC), R_th(JA) | junction temperature, small-signal JFETs rarely need it |

Note: JFETs are depletion-mode and specified with wide min-max spreads on
V_GS(off) and I_DSS (often 5-10x range within one part number); store the
range, never collapse it to a single "typical" value, the spread is exactly
what a builder needs to design a self-bias network from a real part in hand.

**Comparator** (`comparator`, see `src/partinfo/data/parts/comparator/lm311.json`):

| group | parameters | feeds |
|-------|-----------|-------|
| supply | V_s range, I_q | budgeting |
| input | V_os, I_bias | offset / error |
| output | output stage type (open-collector vs push-pull), I_out | pullup/load design |
| speed | response time (propagation delay) | switching speed budget |

Note: don't confuse this with the op-amp core set. A comparator's output
stage topology (open-collector needs an external pullup; push-pull doesn't)
is itself a calc-input, store it as plainly as a number.

Core sets for the remaining classes (MCU, sensor, RF, memory, display,
driver, thyristor) are defined the same way as they are filled in. Follow
the neighbouring entries in the category and the "store the inputs" test above.

## Known gaps: fields no primary datasheet quotes

Some calc-input fields are missing not because nobody looked, but because the
part's primary datasheet genuinely doesn't publish them (common on
abbreviated small-signal sheets). These are tracked in `GAPS.md` rather than
guessed at or left silently blank. If you have bench equipment, closing one
of these with a real measurement is a welcome contribution.

Run `python3 scripts/find_gaps.py [category]` to regenerate an approximate
audit yourself rather than trusting `GAPS.md` is current: it's a substring
check on field names, so cross-reference a hit against the part's rendered
`--specs` output before assuming it's real (it will, for example, flag
`tl431` for "Iq" even though a shunt reference's cathode current already
covers that role under a different name).

## Measuring a gap yourself

If you measure a value, say so in the field itself, e.g.
`"Rth(JA)": "280 C/W (measured, not datasheet)"` -- there's no separate
provenance field for this, so keep the distinction visible inline. Note your
test conditions (Pd, ambient, bias point) the same way the datasheet would.
Remove the entry from `GAPS.md` once it's filled.

A rough starting point for the equipment side, per parameter group:

- **Rth(JC) / Rth(JA)** (thermal resistance): steady-state self-heating test.
  Force a known continuous Pd through the part, let it reach thermal
  equilibrium, then measure junction temperature indirectly via a
  temperature-sensitive electrical parameter (e.g. Vsd or Vbe at a fixed low
  sense current, read immediately after interrupting the heating current) and
  case/ambient temperature with a thermocouple. `Rth = (Tj - Tref) / Pd`.
- **Qg / Qgs / Qgd** (gate charge, MOSFET): constant-current gate-charge test
  -- a constant-current source drives the gate while the drain sinks a fixed
  Id; scope Vgs against time (charge = Ig * t) and read the plateau
  boundaries. This is the standard circuit shown in the "Gate Charge Test
  Circuit" figure of any HEXFET-style datasheet; reuse that topology.
- **Ciss / Coss / Crss**: an LCR meter or impedance analyzer at the
  datasheet's stated bias and frequency (typically 1 MHz, Vgs=0). A curve
  tracer with a CV option works too.
- **Switching times** (td(on), tr, td(off), tf) and **trr/Qrr**: a
  double-pulse (or single resistive-load) switching test with a scope on
  Vgs/Vds/Id -- same topology as the datasheet's switching-waveform figure.
  Needs a fast enough scope/probe for the edge rates involved.
- **Vce(sat) / Vbe(on) / Vf / Vsd** (forward voltages): source-measure at the
  datasheet's stated test current, room temperature; a bench SMU or a
  current-source + DVM is enough.
- **f_T** (transition frequency, BJT): network analyzer / gain-bandwidth
  measurement, or infer from a known-good high-frequency test fixture if you
  don't have a VNA -- flag the method used.
- **Vos / Ibias / CMRR** (op-amp DC precision): needs a low-offset test
  fixture (nulled reference, matched resistor network) and a precision DVM;
  not really doable on a hobbyist bench without care -- treat these as
  lower-priority for self-measurement.
- **Iq / dropout** (regulator): straightforward bench supply + DMM/scope,
  sweeping Vin down until Vout drops out of regulation, or reading quiescent
  current with the output unloaded.

Whatever you measure, describe the setup well enough that someone else could
reproduce or dispute it -- that's the same bar the primary-datasheet rule
already holds everything else to.
