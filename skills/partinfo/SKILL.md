---
name: partinfo
description: Look up electronic component pinouts, specs, and gotchas from the local partinfo reference database. Use when the user asks about a specific part (e.g. NE555, TL072, ESP32, 2N3904, BC547, LM317), needs a pinout or ASCII package diagram, or asks which pin does what on a chip or transistor.
---

# partinfo

`partinfo` is an offline CLI reference for electronic components: pinouts,
key specs, typical applications, and practical gotchas, with ASCII package
diagrams rendered from pin data.

## When to use

- The user names a component and wants its pinout, specs, or how to wire it.
- The user asks "what pin is X on a Y", "is this transistor EBC or CBE",
  "which way round is the LM317", etc.
- The user is searching for a part by function ("a dual low-noise op-amp",
  "a single-supply comparator").

## How to use

Run the CLI; do not read the JSON files directly unless editing the database.

```sh
partinfo <name>            # full entry: pinout, specs, typical use, gotchas
partinfo <name> --pins     # pinout table only
partinfo <name> --ascii    # ascii package diagram
partinfo <name> --specs    # specs: headline table + detailed extras
partinfo <name> --specs -b # --brief: headline specs only, skip the details
partinfo <name> --pkg DIP-8  # restrict to one package
partinfo <name> --json     # machine-readable output
partinfo search <query>    # full-text search across name/tags/description
partinfo list              # list every part id
```

Names are case-insensitive and match the id, canonical name, aliases, or a
manufacturer variant's part number (so `partinfo 555`, `partinfo ne555`, and
`partinfo p2n2222a` all work; the last resolves to the generic `2n2222`).

Search is punctuation-safe: `partinfo search h-bridge`, `i/o expander`,
and `rs-232` all work (terms are matched as literals, not FTS operators).

### Reference topics

Alongside parts, the database carries short reference entries for the
fundamentals: Ohm's law, the voltage divider, RC time constants, the
decibel, E-series values, resistor colour codes, VSWR/return loss, MOSFET
parameters (conduction loss, Tj, gate drive), and the NE555 timing formulas.

```sh
partinfo ref <id>          # show one reference entry
partinfo ref list          # list every reference id
partinfo ref search <query>  # full-text search references
partinfo ref <id> --json   # machine-readable output
```

Reach for these when the question is a calculation or convention ("what
resistor divider gives 3.3V from 5V", "what does a brown-black-red band
mean", "555 frequency for these R and C") rather than about a specific part.

### Doing an actual calculation with a part

Combine a reference formula with a part's stored specs -- don't ask the user
to look up datasheet numbers you already have. Example: is an IRF520 safe at
4A with no heatsink?

```sh
partinfo irf520 --specs        # rds_on_ohm: 0.27, rth_ja_cw: 62.0
partinfo ref mosfet-parameters # P_cond = I_D^2 * R_DS(on); T_j = T_a + P*R_th(JA)
```

`P_cond = 4^2 * 0.27 = 4.3 W`, then `4.3 * 62 = ~267 C` rise -- impossible
without a heatsink (`ref mosfet-parameters` walks the same example).

`--json` gives the exact field names to plug into a formula's variables
without guessing. A handful of universal, condition-free values are typed
directly on `specs` (`rds_on_ohm`, `vgs_th_v`, `hfe_min`/`hfe_max`, `vf_v`,
`iq_ma`, `rth_jc_cw`, `rth_ja_cw`, and others -- see `schema.py`'s `Specs`
model for the full list). Everything else datasheet-specific (Qg, leakage
current, Vce(sat), dropout, and anything that needs a test condition to mean
something) lives in `specs.extra` as a labeled string, still present, just
not typed -- read it the same way, it just isn't a bare number to plug in
blind.

## Notes

- If a lookup misses, run `partinfo search <term>` to find related parts
  before telling the user it is unknown. Do not reach for `--fallback` on
  your own initiative -- it's a deliberate opt-in for when the user
  explicitly wants a guess, not a normal next step after a miss.
  `partinfo <name> --fallback ollama` asks a local model to guess a part it
  doesn't have -- the result is unverified (`source: ollama`), treat it with
  real skepticism and say so. `--fallback claude` is not implemented; it
  exits with an error.
- Curated entries are authoritative. An entry tagged with a non-human
  `source` (a local-model fallback, or a from-scratch AI-authored entry)
  prints a "verify before trusting" warning unless `human_reviewed` is set on
  it (a human has since checked and confirmed the entry); surface the
  warning to the user whenever it appears.
- Watch the gotchas: pin order traps are common (BC547 is C-B-E vs the
  2N3904 E-B-C; the LM317 tab is OUT but the 7805 tab is GND; the 79xx
  regulator pinout differs from the 78xx). The database calls these out.
- Some parts have a manufacturer-dependent pinout (e.g. 2N2222: the common
  convention is E-B-C, but onsemi's P2N2222A is mirrored to C-B-E). The full
  entry shows the common pinout plus a VARIANTS section listing the specific
  parts that differ; always match the user's actual part number.
- To add or correct a part: edit/add a JSON file under
  `src/partinfo/data/parts/<category>/` (in a checkout, not an installed
  copy) then run `partinfo ingest` to rebuild the index.
