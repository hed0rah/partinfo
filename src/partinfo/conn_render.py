"""
connector entry renderer.
formats a Connector for the terminal: an ascii pin-layout diagram (a d-sub /
header face view drawn from `form` + `rows`, or a pre-rendered `ascii`
override), the contact table, variants, and gotchas.
"""

from __future__ import annotations
from .schema import Connector, Contact
from .color import ColorMode, colorize_section, colorize_warning


def _fmt_rows(rows: list[list], gap: int = 2) -> tuple[list[str], int]:
    """format each row as aligned pin labels: right-justified to the widest
    label, joined by `gap` spaces. returns (row_strings, widest_row_width)."""
    pw = max((len(str(p)) for r in rows for p in r), default=1)
    strs = [(" " * gap).join(str(p).rjust(pw) for p in r) for r in rows]
    return strs, max((len(s) for s in strs), default=0)


def _dsub(rows: list[list], pad: int = 3) -> str:
    """D-shell face view: a trapezoid whose top edge is wider than the bottom
    (the sides converge downward), pins centered on each row. plain ascii."""
    n = len(rows)
    strs, base = _fmt_rows(rows)
    if not base:
        return ""
    # inner width of the top (widest) edge; every line below loses one column
    # per side, tapering the frame into a trapezoid.
    total = base + 2 * pad + 2 * (n + 1)
    out = [" " + "_" * (total - 2)]                          # long flat top edge
    for i, s in enumerate(strs):
        indent = i + 1
        out.append(" " * indent + "\\" + s.center(total - 2 * indent - 2) + "/")
    indent = n + 1
    out.append(" " * indent + "\\" + "_" * (total - 2 * indent - 2) + "/")
    return "\n".join(out)


def _header(rows: list[list], pad: int = 3) -> str:
    """rectangular header / IDC box, one or two rows, pins centered. plain ascii.
    for pin headers and ribbon connectors that are NOT D-shells."""
    strs, base = _fmt_rows(rows)
    if not base:
        return ""
    inner = base + 2 * pad
    out = ["  ." + "-" * inner + "."]
    for s in strs:
        out.append("  |" + s.center(inner) + "|")
    out.append("  '" + "-" * inner + "'")
    return "\n".join(out)


def _inline(rows: list[list], pad: int = 3) -> str:
    """single-row flat connector (USB-A, JST, edge card): flatten to one row."""
    return _header([[p for r in rows for p in r]], pad)


def _diagram(c: Connector) -> str:
    if c.ascii:
        return c.ascii
    if not c.rows:
        return ""
    return {"dsub": _dsub, "header": _header, "inline": _inline}.get(c.form, lambda r: "")(c.rows)


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
