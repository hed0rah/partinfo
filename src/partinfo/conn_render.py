"""
connector entry renderer.
formats a Connector for the terminal: an ascii pin-layout diagram (a d-sub /
header face view drawn from `form` + `rows`, or a pre-rendered `ascii`
override), the contact table, variants, and gotchas.
"""

from __future__ import annotations
from .schema import Connector, Contact
from .color import ColorMode, colorize_section, colorize_warning


def _dsub(rows: list[list], cell: int = 3) -> str:
    """face-view trapezoid (D-shell) with pin numbers, one or two rows.
    a schematic layout, not a mechanically exact drawing: pins are shown in
    physical-row order so you can find pin N at a glance."""
    widest = max((len(r) for r in rows), default=0)
    if widest == 0:
        return ""
    inner = widest * cell + 2
    lines = ["  " + "_" * (inner + 2)]
    for i, r in enumerate(rows):
        body = "".join(str(p).rjust(cell) for p in r)
        indent = ((widest - len(r)) * cell) // 2   # stagger a shorter row
        content = (" " * (1 + indent) + body).ljust(inner)
        lft, rgt = ("/", "\\") if i == 0 else ("\\", "/")
        lines.append(f"  {lft}{content}{rgt}")
    lines.append("  " + "-" * (inner + 2))
    return "\n".join(lines)


def _diagram(c: Connector) -> str:
    if c.ascii:
        return c.ascii
    if c.form in ("dsub", "header", "inline") and c.rows:
        return _dsub(c.rows)
    return ""


def _contact_table(contacts: list[Contact]) -> str:
    pw = max([len(str(x.pin)) for x in contacts] + [3])
    nw = max([len(x.name) for x in contacts] + [4])
    sw = max([len(x.signal or "-") for x in contacts] + [6])
    lines = [
        f"  {'PIN':<{pw}}  {'NAME':<{nw}}  {'SIGNAL':<{sw}}  DESCRIPTION",
        f"  {'─' * pw}  {'─' * nw}  {'─' * sw}  {'─' * 11}",
    ]
    for x in contacts:
        lines.append(
            f"  {str(x.pin):<{pw}}  {x.name:<{nw}}  {(x.signal or '-'):<{sw}}  {x.description}"
        )
    return "\n".join(lines)


def render_conn(c: Connector, mode: ColorMode = "off") -> str:
    lines = [f"\n{c.name}"]
    meta = []
    if c.standard:
        meta.append(f"standard: {c.standard}")
    if c.family:
        meta.append(c.family)
    if c.gender:
        meta.append(c.gender)
    if meta:
        lines.append("  " + "    ".join(meta))
    if c.tags:
        lines.append(f"  tags: {', '.join(c.tags)}")
    lines.append(f"\n  {c.description}")

    diag = _diagram(c)
    if diag:
        lines.append(colorize_section("\n── FACE VIEW " + "─" * 57, mode))
        for ln in diag.splitlines():
            lines.append(f"  {ln}")

    lines.append(colorize_section("\n── CONTACTS " + "─" * 58, mode))
    lines.append(_contact_table(c.contacts))

    if c.variants:
        lines.append(colorize_section("\n── VARIANTS " + "─" * 58, mode))
        for v in c.variants:
            lines.append(f"  • {v}")
    if c.gotchas:
        lines.append(colorize_section("\n── GOTCHAS " + "─" * 59, mode))
        for g in c.gotchas:
            lines.append(f"  • {g}")
    if c.related:
        lines.append(f"\n  related: {', '.join(c.related)}")
    if c.see_also_url:
        lines.append(f"  see also: {c.see_also_url}")
    if c.source != "human" and not c.human_reviewed:
        lines.append(colorize_warning(f"\n  [!] source: {c.source} -- verify before trusting", mode))
    return "\n".join(lines)
