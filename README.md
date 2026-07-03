# partinfo

Electronic component reference database with ASCII pinout diagrams.

`partinfo` is an offline command-line reference for common electronic parts:
pinouts, key specs, typical applications, and the gotchas that bite you in
practice. Parts are stored as plain JSON files (the source of truth) and
indexed into SQLite with full-text search.

Built for agent use as much as human use: structured JSON output on every
lookup and a ready-made skill (see [`skills/`](skills/README.md)) so Claude
Code or Codex query partinfo instead of guessing a pinout from memory.

## Why

Datasheets are slow to open and pin numbering traps are easy to forget (the
BC547 is C-B-E, the 2N3904 is E-B-C; the LM317 tab is the output but the 7805
tab is ground). `partinfo` answers those in one command, with the package
drawn in ASCII so you can wire it without opening a PDF.

## Install

```sh
pip install partinfo        # once published
# or, from a checkout:
pip install -e .
```

## Usage

```sh
partinfo ne555              # full entry
partinfo ne555 --pins       # pinout table only
partinfo ne555 --ascii      # ascii package diagram
partinfo lm317 --specs      # key specs only
partinfo search comparator  # full-text search
partinfo list               # list all part ids
partinfo ingest             # rebuild the index from parts/
```

Pin diagrams and warnings are colored by default on a real terminal (pins by
function, warnings in red) and plain everywhere else (piped, redirected, or
read by a script/model). Override with `--color {auto,semantic,minimal,mixed,off}`,
or set `NO_COLOR=1` to force plain output unconditionally.

Unknown part, optional local-model fallback (requires a running Ollama):

```sh
partinfo someobscurepart --fallback ollama --model nemotron-nano-4b
```

Fallback entries are tagged with their source and flagged "verify before
trusting"; only curated entries are treated as authoritative.

## Data model

Each part is one JSON file under `parts/<category>/`. The schema is defined and
validated by Pydantic in `src/partinfo/schema.py`. Key fields:

- `id`, `name`, `aliases`, `full_name`, `manufacturers`, `category`, `tags`
- `packages`: a map of package name (e.g. `DIP-8`) to a pin list, each pin with
  number/name, type, description, and alternate functions
- `specs`: optional, only the fields relevant to the part type
- `typical_application`, `gotchas`, `related`, `datasheet_url`

Add a part by dropping a JSON file in the right category folder and running
`partinfo ingest`. The ASCII diagram is rendered from the pin data
automatically; supply a pre-rendered `ascii` string on a package only to
override.

## License

MIT
