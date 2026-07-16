---
name: partinfo
description: Look up electronic component and connector/cable pinouts, specs, and gotchas from the local partinfo reference database. Use when the user asks about a specific part (e.g. NE555, TL072, ESP32, 2N3904) or a connector/cable (e.g. OBD-II, USB-C, DB9, HDMI, eurorack power, MIDI DIN), needs a pinout or ASCII diagram, or asks which pin does what on a chip, transistor, or connector.
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
partinfo <name>            # full entry: diagram + pinout + specs + gotchas + more
partinfo <name> --ascii    # just the ascii package diagram
partinfo <name> --pins     # just the pinout table
partinfo <name> --specs    # just the specs (add -b / --brief for headline only)
partinfo <name> --gotchas  # just the gotchas
partinfo <name> --ascii --pins   # SECTION FLAGS COMBINE: diagram + pin table, nothing else
partinfo <name> --pkg DIP-8      # restrict to one package
partinfo <name> --json           # machine-readable output (field names for calcs)
partinfo search <query>    # full-text search across name/tags/description
partinfo list              # list every part id
partinfo gallery [filter]  # render just the ascii diagrams for many parts at once
                           #   (optional filter by id / category / template, e.g. `gallery mosfet`)
```

Bare `partinfo <name>` prints the whole entry, diagram included. The section flags
(`--ascii`, `--pins`, `--specs`, `--gotchas`) are **combinable filters**: pass any
subset to print only those sections (e.g. `--ascii --pins` for a diagram plus the pin
table). There is no `--full`; bare is full. `partinfo conn <id>` works the same way.

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

### Connector / cable pinouts

Physical connectors (OBD-II, DB9 / serial, ...) live in their own `conn`
namespace -- a connector is a pinout on a mechanical interface, not a
component. Each entry renders an ascii face-view diagram plus a contact table.

```sh
partinfo conn <id>            # full entry: ascii face view + contact table + gotchas
partinfo conn list            # list every connector id
partinfo conn search <query>  # full-text search connectors
partinfo conn gallery [filter]  # render every connector's face-view diagram (filter by id/standard/form)
partinfo conn <id> --json     # machine-readable output
```

Reach for these when the user is probing a cable or connector ("which OBD-II
pin is CAN-H", "DB9 pinout", "is pin 5 ground"), especially during hardware
bring-up with a multimeter on an unknown connector.

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
- To add or correct a part, see the section below.

## Adding or correcting a part

One JSON file per part under `src/partinfo/data/parts/<category>/`, validated
against `src/partinfo/schema.py`. Directory names are cosmetic -- the `category`
field is authoritative, and the tree mixes singular and plural dir names
(`sensor` vs `sensors`, etc.), so check BOTH when looking for an existing entry.
Full rules are in `CONTRIBUTING.md`; the non-negotiables:

- **Primary datasheet only.** Verify pins and specs against the manufacturer's
  own PDF, never an aggregator (alldatasheet, lcsc, octopart). Cite it in
  `datasheet_url`.
- **Position first, names second.** Confirm which physical pin *number* is which
  function from the actual package drawing -- a pinout is right or wrong at the
  pin-number level; labels are cosmetic on top. (This rule exists because it has
  caught real bugs: cd4066, tl431, bd139 all shipped with transposed pins until
  a datasheet read fixed them.)
- **`verified: true` only when a human or agent read the primary sheet and
  checked the pins against it** -- not from memory, not "an aggregator agreed."
  An honest `false` with a `notes` reason beats a hopeful `true`. `source` stays
  a permanent record of who wrote the entry; `human_reviewed: true` records that
  a human has since confirmed a non-human-sourced one.
- **Store the calculation inputs, not the datasheet.** Meet the core-parameter
  set for the device class (CONTRIBUTING.md): well-known typed values go in
  `specs`, everything else in `specs.extra`. If a common calc for the part needs
  an input you didn't store, the entry is incomplete.
- **`datasheet_name`** (per pin) = the verbatim vendor label, set only when it
  differs from the house `name`. **`variants`** = a specific MPN whose *physical*
  pinout differs from the common one; never let a variant mask a wrong pinout.

Workflow:

```sh
# 1. before adding, catch an id collision (checks singular + plural dirs)
find src/partinfo/data/parts -name '*.json' -exec basename {} \; | sort | uniq -d
# 2. write/edit the JSON in a checkout (not an installed copy)
# 3. rebuild the derived index
partinfo ingest
# 4. eyeball the render -- pinout, specs, gotchas all look right?
partinfo <id>              # bare prints everything: diagram, pinout, specs, gotchas
# 5. commit (voice per TASTE.md) and push to origin/main (this repo is public)
```

Archive the source datasheet PDF to the private inventory repo at
`parts-db/datasheets/<category>/` as `<part>-<source>.pdf` -- that tree is
gitignored, so the binary PDFs stay on disk and out of the public repo.
