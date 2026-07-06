"""
pretty-print formatting for Part entries.
pulled out of cli.py so it's a plain library call (from partinfo.render import
fmt_full) for scripts and skills, not something that requires shelling out to
the CLI and parsing text.
"""

from __future__ import annotations
import shutil
import textwrap
from .schema import Part
from .color import (
    ColorMode, colorize_warning, colorize_section, colorize_pin, colorize_dim,
)


def fmt_pins(part: Part, package: str | None = None, mode: ColorMode = "off") -> str:
    lines = []
    pkgs = part.packages
    if package:
        pkgs = {k: v for k, v in pkgs.items() if k.lower() == package.lower()}
    for pkg_name, pkg in pkgs.items():
        lines.append(f"\n  {pkg_name}")
        lines.append(colorize_dim(f"  {'PIN':<6} {'NAME':<16} {'TYPE':<14} DESCRIPTION", mode))
        lines.append(colorize_dim(f"  {'─'*6} {'─'*16} {'─'*14} {'─'*40}", mode))
        for p in sorted(pkg.pins, key=lambda x: int(x.pin) if isinstance(x.pin, int) else 0):
            alt = f"  [{', '.join(p.alternate)}]" if p.alternate else ""
            dsn = f"  (datasheet: {p.datasheet_name})" if p.datasheet_name else ""
            name = colorize_pin(f"{p.name:<16}", p.type, mode)   # padded then colored
            lines.append(f"  {str(p.pin):<6} {name} {p.type:<14} {p.description}{dsn}{alt}")
    return "\n".join(lines)


def _num(x) -> str:
    """render a number without a pointless trailing .0 (100.0 -> '100'; 0.27 stays)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


def _power(mw: float | None) -> str | None:
    """mW, promoted to W once it gets big enough to read cleaner (60000 mW -> 60 W)."""
    if mw is None:
        return None
    return f"{_num(mw / 1000)} W" if mw >= 1000 else f"{_num(mw)} mW"


def _range(lo, hi, unit: str = "") -> str | None:
    """format a min/max pair, tolerating either half being absent -- never
    interpolate a bare None into the string just because the other half exists."""
    if lo is None and hi is None:
        return None
    if lo is not None and hi is not None:
        return f"{_num(lo)}{unit}-{_num(hi)}{unit}"
    return f"{_num(hi)}{unit} max" if lo is None else f"{_num(lo)}{unit} min"


def _typed_fields(s) -> dict[str, str]:
    """the curated, short-labeled headline specs -- the ones that align into a
    clean table. everything datasheet-specific (values that need a test condition)
    lives in `extra` instead and shows in the detail block."""
    fields = {
        "supply voltage":    _range(s.vs_min_v, s.vs_max_v, "V"),
        "supply (typ)":      f"{_num(s.vs_typ_v)} V" if s.vs_typ_v is not None else None,
        "quiescent current": f"{_num(s.iq_ma)} mA" if s.iq_ma is not None else None,
        "gain":              _range(s.gain_db_min, s.gain_db_max, " dB"),
        "bandwidth":         f"{s.bw_hz/1e3:.0f} kHz" if s.bw_hz else None,
        "max freq":          f"{s.freq_max_hz/1e6:.0f} MHz" if s.freq_max_hz else None,
        "output power":      _power(s.pout_mw),
        "max dissipation":   _power(s.pd_max_mw),
        "hFE":               _range(s.hfe_min, s.hfe_max),
        "Vce(sat)":          f"{_num(s.vce_sat_v)} V" if s.vce_sat_v is not None else None,
        "IDSS":              f"{_num(s.idss_ma)} mA" if s.idss_ma is not None else None,
        "Vgs(off)":          f"{_num(s.vgs_off_v)} V" if s.vgs_off_v is not None else None,
        "Rds(on)":           f"{_num(s.rds_on_ohm)} Ω" if s.rds_on_ohm is not None else None,
        "Vgs(th)":           f"{_num(s.vgs_th_v)} V" if s.vgs_th_v is not None else None,
        "Vf":                f"{_num(s.vf_v)} V" if s.vf_v is not None else None,
        "Rth(JC)":           f"{_num(s.rth_jc_cw)} °C/W" if s.rth_jc_cw is not None else None,
        "Rth(JA)":           f"{_num(s.rth_ja_cw)} °C/W" if s.rth_ja_cw is not None else None,
        "flash":             f"{s.flash_kb} KB" if s.flash_kb else None,
        "RAM":               f"{s.ram_kb} KB" if s.ram_kb else None,
        "EEPROM":            f"{s.eeprom_b} B" if s.eeprom_b else None,
        "CPU":               f"{s.cpu_mhz} MHz" if s.cpu_mhz else None,
        "GPIO":              f"{s.gpio_count}" if s.gpio_count is not None else None,
    }
    return {k: v for k, v in fields.items() if v}


def _detail_block(detail: list[tuple[str, str]], mode: ColorMode) -> list[str]:
    """the conditioned `extra` specs, always tidy: short labels align in a column
    with the value wrapped under it; long labels get their own line, value indented."""
    width = min(shutil.get_terminal_size((100, 24)).columns, 100)
    lw = min(max(len(k) for k, _ in detail), 22)
    out: list[str] = []
    for k, v in detail:
        if len(k) <= lw:
            vw = max(24, width - lw - 4)
            wrapped = textwrap.wrap(v, vw) or [""]
            out.append(f"  {colorize_dim(f'{k:<{lw}}', mode)}  {wrapped[0]}")
            out += [f"  {' '*lw}  {c}" for c in wrapped[1:]]
        else:
            out.append(f"  {colorize_dim(k, mode)}")
            out += [f"      {c}" for c in (textwrap.wrap(v, max(24, width - 6)) or [""])]
    return out


def fmt_specs(part: Part, mode: ColorMode = "off", brief: bool = False) -> str:
    if not part.specs:
        return "  no specs recorded"
    s = part.specs
    # headline = typed fields NOT already restated in extra (extra's version has
    # the test conditions, so it wins and stays in the detail -- no label twice).
    extra_labels = {k.lower() for k in s.extra}
    headline = {k: v for k, v in _typed_fields(s).items() if k.lower() not in extra_labels}
    detail = [(k, str(v)) for k, v in s.extra.items()]
    if not headline and not detail:
        return "  no specs recorded"

    lines: list[str] = []
    if headline:
        lw = min(max(len(k) for k in headline), 24)
        lines.append(colorize_dim(f"  {'SPEC':<{lw}}  VALUE", mode))
        lines.append(colorize_dim(f"  {'─'*lw}  {'─'*26}", mode))
        for k, v in headline.items():
            lines.append(f"  {colorize_dim(f'{k:<{lw}}', mode)}  {v}")
    # --brief drops the detail only when there's a headline to stand on its own;
    # a part whose specs live entirely in extra still shows them.
    if detail and not (brief and headline):
        if headline:
            lines.append(colorize_dim("\n  detail " + "─" * 40, mode))
        lines += _detail_block(detail, mode)
    return "\n".join(lines)


def _section(title: str, width: int, mode: ColorMode) -> str:
    bar = f"\n── {title} " + "─" * width
    return colorize_section(bar, mode)


def fmt_full(part: Part, mode: ColorMode = "off") -> str:
    lines = []
    lines.append(f"\n{part.name}  --  {part.full_name}")
    if part.aliases:
        lines.append(f"  aliases: {', '.join(part.aliases)}")
    if part.manufacturers:
        lines.append(f"  mfr:     {', '.join(part.manufacturers)}")
    lines.append(f"  tags:    {', '.join(part.tags)}")
    lines.append(f"\n  {part.description}")
    lines.append(_section("PINOUT", 60, mode))
    lines.append(fmt_pins(part, mode=mode))
    if part.specs:
        lines.append(_section("SPECS", 61, mode))
        lines.append(fmt_specs(part, mode))
    if part.typical_application:
        lines.append(_section("TYPICAL APPLICATION", 47, mode))
        lines.append(f"  {part.typical_application}")
    if part.gotchas:
        lines.append(_section("GOTCHAS", 59, mode))
        for g in part.gotchas:
            lines.append(f"  • {g}")
    if part.variants:
        lines.append(_section("VARIANTS", 58, mode))
        lines.append("  the common pinout is shown above; these manufacturer parts differ:")
        for v in part.variants:
            order = "-".join(p.name for p in v.pins)
            badge = " [verified]" if v.verified else ""
            lines.append(f"\n  {v.mpn} ({v.manufacturer}) -- {v.package}: {order}{badge}")
            if v.note:
                lines.append(f"    {v.note}")
            if v.datasheet_url:
                lines.append(f"    datasheet: {v.datasheet_url}")
    if part.related:
        lines.append(f"\n  related: {', '.join(part.related)}")
    if part.datasheet_url:
        lines.append(f"  datasheet: {part.datasheet_url}")
    if part.source != "human" and not part.human_reviewed:
        warn = f"\n  [!] source: {part.source} -- verify before trusting"
        lines.append(colorize_warning(warn, mode))
    elif not part.verified:
        warn = "\n  [!] unverified: hand-entered, not yet checked against the datasheet"
        lines.append(colorize_warning(warn, mode))
    return "\n".join(lines)


def fmt_ascii(part: Part, package: str | None = None, mode: ColorMode = "off") -> str:
    from .ascii_render import render as render_ascii

    lines = []
    for pkg_name, pkg in part.packages.items():
        if package and pkg_name.lower() != package.lower():
            continue
        lines.append(f"\n  {part.name} -- {pkg_name}")
        lines.append(render_ascii(pkg, part.name, mode))
    return "\n".join(lines)
