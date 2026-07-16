# partinfo

Datasheet-verified electronic component pinouts, specs, and ASCII diagrams — in your terminal, fully offline.

`partinfo` is an offline command-line reference for electronic parts **and** connectors: pinouts, key specs, typical applications, and the gotchas that bite you in practice. Every entry is a hand-curated, datasheet-verified JSON file (the source of truth), indexed into SQLite with full-text search. **228 parts, 25 connectors, and a library of formula references** — all bundled, no network needed.

Built for agents as much as humans: structured `--json` on every lookup and a ready-made [skill](skills/README.md) so Claude Code or Codex reach for partinfo's *verified* numbers instead of hallucinating a pinout — or a thermal resistance — from memory.

## Why

Datasheets are slow to open and pin-numbering traps are easy to forget (the BC547 is C-B-E, the 2N3904 is E-B-C; the LM317 tab is the output but the 7805 tab is ground). `partinfo` answers those in one command, with the package drawn in ASCII so you can wire it without opening a PDF.

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
partinfo ref mosfet-parameters  # formulas + a variable legend

partinfo gallery                # every part's diagram, for a scroll
```

### The diagram is generated, not drawn

The ASCII pinout is rendered from the *same* verified pin table as the specs, so the picture and the data can't disagree. Pins are colored by function on a real terminal and drop to plain when piped or read by a script/model — override with `--color {auto,semantic,minimal,mixed,off}` or `NO_COLOR=1`.

### It computes, not just looks up

Every part stores its **calculation inputs** (`rds_on_ohm`, `rth_ja_cw`, ...) and the reference library stores the **formulas**, so real questions get answered from verified numbers. *"Is an IRF520 safe switching 3 A in still air?"* → pull `Rds(on) = 0.27 Ω` and `Rth(JA) = 62 °C/W`, apply `P = I²·R` and `Tj = Ta + P·Rth(JA)` → `Tj ≈ 176 °C`, past the limit. The datasheet's 9 A headline is a thermal lie without a heatsink, and partinfo plus one formula proves it. `--json` hands the field names straight to a formula's variables — which is exactly how the [skill](skills/README.md) lets an AI do this grounded, instead of guessing.

## Data model

Each part is one JSON file validated by a Pydantic schema — `packages` (pins with number / name / type / description), `specs`, `gotchas`, `related`, `datasheet_url`. Connectors and references use the same approach, so every entry — yours or mine — is structurally identical, and diagrams render straight from the pin data. Add a part by dropping a JSON file in its category folder and running `partinfo ingest`.

The JSON ships inside the package; the SQLite index is a derived cache at `~/.local/share/partinfo/parts.db`, built automatically on first use.

## License

MIT
