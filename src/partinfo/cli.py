"""
partinfo CLI
usage:
  partinfo <name>              full entry
  partinfo <name> --pins       pinout table only
  partinfo <name> --ascii      ascii package diagram
  partinfo <name> --specs      key specs only
  partinfo <name> --color MODE force a color mode: auto, semantic, minimal, mixed, off
  partinfo search <query>      full-text search
  partinfo ingest              rebuild parts.db from parts/ and references/
  partinfo list                list all part ids
  partinfo ref <id>            show a reference entry (fundamentals)
  partinfo ref list            list all reference ids
  partinfo ref search <query>  full-text search references

Formatting logic lives in render.py -- this module is argparse wiring only.
"""

from __future__ import annotations
import argparse
import sys
from .db import (
    lookup, search, ingest, all_ids,
    ref_lookup, ref_search, ref_all_ids,
)
from .schema import Part
from .color import resolve_mode
from .render import fmt_pins, fmt_specs, fmt_full, fmt_ascii
from .ref_render import render_ref


def _ollama_fallback(query: str, model: str) -> Part | None:
    try:
        import subprocess
        import json as _json
        schema_hint = (
            "Return ONLY valid JSON matching this structure (omit null fields):\n"
            '{"id":"<slug>","name":"<NAME>","full_name":"...","manufacturers":[],'
            '"category":"other","tags":[],"description":"...",'
            '"packages":{"<PKG>":{"template":"dip","pin_count":8,"pins":['
            '{"pin":1,"name":"X","type":"input","description":"..."}]}},'
            '"specs":{},"typical_application":"...","gotchas":[],"related":[],'
            '"datasheet_url":null,"source":"ollama"}'
        )
        prompt = f"Electronic component datasheet for {query}.\n{schema_hint}"
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=60
        )
        raw = result.stdout.strip()
        # extract JSON block if model wraps in prose
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1:
            return None
        data = _json.loads(raw[start:end])
        return Part(**data)
    except Exception as e:
        print(f"  ollama fallback failed: {e}", file=sys.stderr)
        return None


def main():
    p = argparse.ArgumentParser(
        prog="partinfo",
        description="electronic component reference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # first positional is a part name, or a command: ingest, list, search
    p.add_argument("part", nargs="?", help="part name/id, or a command: ingest, list, search")
    p.add_argument("rest", nargs="*", help="search query (when part is 'search')")
    p.add_argument("--pins",  action="store_true", help="pinout only")
    p.add_argument("--ascii", action="store_true", help="ascii package diagram")
    p.add_argument("--specs", action="store_true", help="specs only")
    p.add_argument("--pkg",   help="filter to specific package (e.g. DIP-8)")
    p.add_argument("--fallback", choices=["ollama", "claude"], help="fallback if not in db")
    p.add_argument("--model", default="nemotron-nano-4b", help="ollama model for fallback")
    p.add_argument("--json",  action="store_true", help="raw JSON output")
    p.add_argument("--color", choices=["auto", "semantic", "minimal", "mixed", "off"],
                    default="auto", help="color mode (default: auto -- color on a real terminal, off otherwise)")

    args = p.parse_args()
    color_mode = resolve_mode(args.color)

    if args.part == "ingest":
        n, errors = ingest()
        print(f"ingested {n} parts")
        if errors:
            print(f"\n{len(errors)} file(s) failed and are NOT in the index:", file=sys.stderr)
            for e in errors:
                print(f"  {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.part == "list":
        for pid in all_ids():
            print(pid)
        return

    if args.part == "ref":
        sub = args.rest[0] if args.rest else None
        if sub == "list":
            for rid in ref_all_ids():
                print(rid)
            return
        if sub == "search":
            query = " ".join(args.rest[1:])
            if not query:
                print("usage: partinfo ref search <query>", file=sys.stderr)
                sys.exit(1)
            results = ref_search(query)
            if not results:
                print("no results")
                return
            for r in results:
                print(f"  {r.id:<24} {r.topic:<10} {r.summary[:60]}")
            return
        if not sub:
            print("usage: partinfo ref <id> | ref list | ref search <query>", file=sys.stderr)
            sys.exit(1)
        ref = ref_lookup(sub)
        if not ref:
            print(f"  not found: {sub}", file=sys.stderr)
            similar = ref_search(sub, limit=5)
            if similar:
                print("  similar references:")
                for r in similar:
                    print(f"    partinfo ref {r.id}")
            sys.exit(1)
        if args.json:
            print(ref.model_dump_json(indent=2, exclude_none=True))
            return
        print(render_ref(ref, color_mode))
        return

    if args.part == "search":
        query = " ".join(args.rest)
        if not query:
            print("usage: partinfo search <query>", file=sys.stderr)
            sys.exit(1)
        results = search(query)
        if not results:
            print("no results")
            return
        for r in results:
            print(f"  {r.id:<20} {r.name:<12} {r.category:<20} {r.description[:60]}")
        return

    if not args.part:
        p.print_help()
        return

    part = lookup(args.part)

    if not part:
        print(f"  not found: {args.part}", file=sys.stderr)
        if args.fallback == "claude":
            print("  --fallback claude is not implemented yet", file=sys.stderr)
            sys.exit(1)
        if args.fallback == "ollama":
            print(f"  querying {args.model}...", file=sys.stderr)
            part = _ollama_fallback(args.part, args.model)
            if not part:
                sys.exit(1)
        else:
            similar = search(args.part, limit=5)
            if similar:
                print("  similar parts in db:")
                for r in similar:
                    print(f"    partinfo {r.id}")
            sys.exit(1)

    if args.json:
        print(part.model_dump_json(indent=2, exclude_none=True))
        return

    if args.ascii:
        print(fmt_ascii(part, args.pkg, color_mode))
        return

    if args.pins:
        print(fmt_pins(part, args.pkg, color_mode))
        return

    if args.specs:
        print(fmt_specs(part))
        return

    print(fmt_full(part, color_mode))


if __name__ == "__main__":
    main()
