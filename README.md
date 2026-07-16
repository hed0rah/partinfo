# partinfo

Datasheet-verified electronic component pinouts, specs, and ASCII diagrams in your terminal, offline.

`partinfo` is an offline command-line reference for electronic parts and connectors: pinouts, key specs, typical applications, and the gotchas that catch you in practice. Every entry is a hand-curated JSON file checked against a datasheet, indexed into SQLite with full-text search. 228 parts, 25 connectors, and a library of formula references ship in the package; no network needed.

Structured `--json` on every lookup, plus a bundled skill (below), so Claude Code or Codex query partinfo for a verified number instead of guessing a pinout (or a thermal resistance) from memory.

## Why

Datasheets are slow to open and pin-numbering traps are easy to forget: the BC547 is C-B-E, the 2N3904 is E-B-C; the LM317 tab is the output but the 7805 tab is ground. `partinfo` answers those in one command, with the package drawn in ASCII so you can wire it without opening a PDF.

## Install

```sh
pip install partinfo
```

## Usage

```sh
partinfo ne555                  # full entry
partinfo irlz44n --ascii        # ASCII package diagram
partinfo lm317 --specs          # key specs only
partinfo search "can transceiver"

# connectors & cables
partinfo conn obd-ii            # OBD-II / DB9 / USB-C / eurorack power / MIDI ...
partinfo conn gallery           # every connector diagram

# formula references
partinfo ref list               # ohms-law, rc-time-constant, mosfet-parameters, ne555-formulas ...
partinfo ref mosfet-parameters  # formulas with a variable legend

partinfo gallery                # every part diagram, to scroll
```

Pins are colored by function on a real terminal and drop to plain when piped or read by a script or model. Override with `--color {auto,semantic,minimal,mixed,off}` or `NO_COLOR=1`.

## Use it as a Claude Code / Codex skill

partinfo ships a skill so an agent reaches for its verified data instead of recalling a pinout from training. After installing:

```sh
partinfo skill install          # copies the skill into ~/.claude/skills and/or ~/.codex/skills (asks first)
```

A fresh session, asked "show me the IRF520 pinout and whether it survives 3 A in still air," then runs partinfo for the diagram and the real thermal numbers and does the math, instead of guessing.

## Diagrams are rendered from the pin data

The ASCII pinout is generated from the same pin table as the specs, so the picture and the data stay in sync. Supply a pre-rendered `ascii` string on a package only to override.

## It computes, not just looks up

Each part stores its calculation inputs (`rds_on_ohm`, `rth_ja_cw`, ...) and the reference library stores the formulas, so a question gets answered from verified numbers. For "is an IRF520 safe switching 3 A in still air?", partinfo supplies `Rds(on) = 0.27 Ω` and `Rth(JA) = 62 °C/W`; applying `P = I²·R` and `Tj = Ta + P·Rth(JA)` gives `Tj ≈ 176 °C`, over the limit. The 9 A on the datasheet front page is a rating that needs a heatsink, and one formula shows it. `--json` hands the field names straight to a formula's variables.

## Data model

Each part is one JSON file validated by a Pydantic schema: `packages` (pins with number, name, type, description), `specs`, `gotchas`, `related`, `datasheet_url`. Connectors and references use the same approach, so every entry is structurally identical and diagrams render from the pin data. Add a part by dropping a JSON file in its category folder and running `partinfo ingest`.

The JSON ships inside the package; the SQLite index is a derived cache at `~/.local/share/partinfo/parts.db`, built on first use.

## License

MIT
