"""
reference entry renderer.
formats a RefEntry for the terminal: summary, prose body, formulas with a
variable legend, aligned tables, worked examples, and gotchas.
"""

from __future__ import annotations
from .schema import RefEntry, Formula, RefTable
from .color import ColorMode, colorize_section, colorize_warning


def _render_table(t: RefTable) -> str:
    cols = len(t.headers)
    widths = [len(h) for h in t.headers]
    for row in t.rows:
        for i in range(cols):
            cell = str(row[i]) if i < len(row) else ""
            widths[i] = max(widths[i], len(cell))
    lines = []
    if t.title:
        lines.append(f"  {t.title}")
    head = "  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(t.headers))
    sep = "  " + "  ".join("─" * widths[i] for i in range(cols))
    lines.append(head)
    lines.append(sep)
    for row in t.rows:
        cells = [(str(row[i]) if i < len(row) else "").ljust(widths[i]) for i in range(cols)]
        lines.append("  " + "  ".join(cells))
    return "\n".join(lines)


def _render_formula(f: Formula) -> str:
    lines = [f"    {f.expr}"]
    if f.description:
        lines.append(f"      {f.description}")
    for v in f.vars:
        unit = f" [{v.unit}]" if v.unit else ""
        lines.append(f"        {v.symbol:<6} {v.meaning}{unit}")
    return "\n".join(lines)


def render_ref(ref: RefEntry, mode: ColorMode = "off") -> str:
    lines = []
    lines.append(f"\n{ref.title}")
    lines.append(f"  topic: {ref.topic}    tags: {', '.join(ref.tags)}")
    lines.append(f"\n  {ref.summary}")
    if ref.body:
        lines.append("")
        for ln in ref.body.rstrip().splitlines():
            lines.append(f"  {ln}" if ln else "")
    if ref.formulas:
        lines.append(colorize_section("\n── FORMULAS " + "─" * 58, mode))
        for f in ref.formulas:
            lines.append(_render_formula(f))
            lines.append("")
        lines.pop()
    if ref.tables:
        lines.append(colorize_section("\n── TABLES " + "─" * 60, mode))
        for t in ref.tables:
            lines.append(_render_table(t))
            lines.append("")
        lines.pop()
    if ref.examples:
        lines.append(colorize_section("\n── EXAMPLES " + "─" * 58, mode))
        for ex in ref.examples:
            lines.append(f"  • {ex}")
    if ref.gotchas:
        lines.append(colorize_section("\n── GOTCHAS " + "─" * 59, mode))
        for g in ref.gotchas:
            lines.append(f"  • {g}")
    if ref.related:
        lines.append(f"\n  related: {', '.join(ref.related)}")
    if ref.see_also_url:
        lines.append(f"  see also: {ref.see_also_url}")
    if ref.source != "human" and not ref.human_reviewed:
        warn = f"\n  [!] source: {ref.source} -- verify before trusting"
        lines.append(colorize_warning(warn, mode))
    return "\n".join(lines)
