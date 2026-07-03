"""
pretty-print formatting for Part entries.
pulled out of cli.py so it's a plain library call (from partinfo.render import
fmt_full) for scripts and skills, not something that requires shelling out to
the CLI and parsing text.
"""

from __future__ import annotations
from .schema import Part
from .color import ColorMode, colorize_warning, colorize_section


def fmt_pins(part: Part, package: str | None = None, mode: ColorMode = "off") -> str:
    lines = []
    pkgs = part.packages
    if package:
        pkgs = {k: v for k, v in pkgs.items() if k.lower() == package.lower()}
    for pkg_name, pkg in pkgs.items():
        lines.append(f"\n  {pkg_name}")
        lines.append(f"  {'PIN':<6} {'NAME':<16} {'TYPE':<14} DESCRIPTION")
        lines.append(f"  {'─'*6} {'─'*16} {'─'*14} {'─'*40}")
        for p in sorted(pkg.pins, key=lambda x: int(x.pin) if isinstance(x.pin, int) else 0):
            alt = f"  [{', '.join(p.alternate)}]" if p.alternate else ""
            dsn = f"  (datasheet: {p.datasheet_name})" if p.datasheet_name else ""
            lines.append(f"  {str(p.pin):<6} {p.name:<16} {p.type:<14} {p.description}{dsn}{alt}")
    return "\n".join(lines)


def fmt_specs(part: Part) -> str:
    if not part.specs:
        return "  no specs recorded"
    lines = []
    s = part.specs
    fields = {
        "supply voltage":   f"{s.vs_min_v}V – {s.vs_max_v}V" if s.vs_min_v else None,
        "quiescent current": f"{s.iq_ma} mA" if s.iq_ma else None,
        "gain":             f"{s.gain_db_min} – {s.gain_db_max} dB" if s.gain_db_min else None,
        "bandwidth":        f"{s.bw_hz/1e3:.0f} kHz" if s.bw_hz else None,
        "max freq":         f"{s.freq_max_hz/1e6:.0f} MHz" if s.freq_max_hz else None,
        "output power":     f"{s.pout_mw} mW" if s.pout_mw else None,
        "max dissipation":  f"{s.pd_max_mw} mW" if s.pd_max_mw else None,
        "hFE":              f"{s.hfe_min} – {s.hfe_max}" if s.hfe_min else None,
        "IDSS":             f"{s.idss_ma} mA" if s.idss_ma else None,
        "Vgs(off)":         f"{s.vgs_off_v} V" if s.vgs_off_v else None,
        "Rds(on)":          f"{s.rds_on_ohm} Ω" if s.rds_on_ohm else None,
        "Vgs(th)":          f"{s.vgs_th_v} V" if s.vgs_th_v else None,
        "flash":            f"{s.flash_kb} KB" if s.flash_kb else None,
        "RAM":              f"{s.ram_kb} KB" if s.ram_kb else None,
        "CPU":              f"{s.cpu_mhz} MHz" if s.cpu_mhz else None,
        "GPIO":             f"{s.gpio_count}" if s.gpio_count else None,
        "Vf":               f"{s.vf_v} V" if s.vf_v else None,
    }
    # if extra carries a matching label (usually with test conditions the
    # bare typed number doesn't), let extra's richer version win the display
    # -- the typed field still exists for --json/querying, just not shown twice
    for label, val in fields.items():
        if val and label not in s.extra:
            lines.append(f"  {label:<22} {val}")
    for k, v in s.extra.items():
        lines.append(f"  {k:<22} {v}")
    return "\n".join(lines) if lines else "  no specs recorded"


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
        lines.append(fmt_specs(part))
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
