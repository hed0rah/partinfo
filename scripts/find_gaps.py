#!/usr/bin/env python3
"""Report which calc-input fields (CONTRIBUTING.md) look missing per part.

Approximate: checks specs + specs.extra key names for a substring, the same
way the fill-spec passes were audited. It will false-positive on parts that
store a field under an unexpected name (e.g. tl431's cathode current instead
of "Iq") -- cross-check against GAPS.md and the part's rendered --specs
output before assuming a hit is a real gap.

Usage:
    python3 scripts/find_gaps.py [category]

With no argument, reports every category in CHECKS.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (label, substrings) -- a part "has" a check if any key (specs top-level or
# specs.extra) contains one of these substrings, case-insensitive.
CHECKS = {
    "transistor_mosfet": [
        ("Rth(JC)/Rth(JA)", ("rth",)),
        ("Qg/Qgs/Qgd", ("qg",)),
        ("Ciss/Coss/Crss", ("ciss", "coss", "crss")),
        ("switching times", ("td(on)", "tr", "td(off)", "tf", "ton", "toff")),
        ("Vsd", ("vsd",)),
        ("trr", ("trr",)),
    ],
    "power": [
        ("Rth(JC)/Rth(JA)", ("rth",)),
        ("Iq", ("iq", "iadj", "icc")),
        ("Vin_max", ("vin", "vcc_abs_max", "input max")),
        ("dropout/Vsat/SW Ron", ("dropout", "vsat", "sw ron", "ron")),
    ],
    "transistor_bjt": [
        ("Vce(sat)", ("vce(sat)", "vce_sat")),
        ("Vbe(on)", ("vbe(on)", "vbe_on")),
        ("f_T", ("f_t", "transition frequency", "freq_max_hz")),
        ("Rth(JC)/Rth(JA)", ("rth",)),
    ],
    "transistor_germanium": [
        ("Vce(sat)/Vbe(sat)", ("vce(sat)", "vce_sat", "vbe(sat)", "vbe_sat")),
        ("hFE", ("hfe",)),
        ("ICBO/IEBO leakage", ("icbo", "iebo")),
        ("Rth (power parts)", ("rth",)),
    ],
    "diode": [
        ("Vf", ("vf",)),
        ("Ir", ("ir",)),
        ("Vz/Pz/Zzt (zener)", ("vz", "pz", "zzt")),
        ("Rth (power)", ("rth",)),
    ],
    "opamp": [
        ("Vos", ("vos",)),
        ("Ibias", ("ibias",)),
        ("Iout", ("iout",)),
        ("CMRR", ("cmrr",)),
    ],
    "transistor_jfet": [
        ("Vgs(off)", ("vgs_off", "vgs(off)")),
        ("IDSS", ("idss",)),
        ("gfs", ("gfs",)),
        ("Rth (power parts)", ("rth",)),
    ],
    "comparator": [
        ("Vos", ("vos", "input_offset")),
        ("Ibias", ("ibias", "input_bias")),
        ("output type", ("output_type", "open-collector", "open collector", "push-pull", "push pull")),
        ("response time", ("response_time", "response time", "propagation")),
    ],
}


def load_parts():
    parts = {}
    for f in (REPO_ROOT / "src" / "partinfo" / "data" / "parts").glob("**/*.json"):
        d = json.loads(f.read_text())
        parts[d["id"]] = d
    return parts


def has(part, *substrings):
    specs = part.get("specs") or {}
    blob = " ".join(
        [k.lower() for k, v in specs.items() if v is not None]
        + [k.lower() for k in (specs.get("extra") or {})]
    )
    return any(s in blob for s in substrings)


def main():
    requested = sys.argv[1:] or list(CHECKS)
    parts = load_parts()
    for category in requested:
        checks = CHECKS.get(category)
        if checks is None:
            print(f"no checks defined for category {category!r}", file=sys.stderr)
            continue
        members = [p for p in parts.values() if p["category"] == category]
        print(f"## {category} ({len(members)} parts)")
        for label, substrings in checks:
            missing = sorted(p["id"] for p in members if not has(p, *substrings))
            print(f"  {label}: missing {len(missing)}/{len(members)} {missing}")
        print()


if __name__ == "__main__":
    main()
