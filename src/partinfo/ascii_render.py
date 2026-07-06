"""
ascii package diagram renderer.
given a Package, draws a human-readable pinout diagram.
pre-rendered ascii stored in package.ascii takes priority -- renderer is
the fallback for packages without a stored diagram. pre-rendered diagrams
are never colored (they're free-form strings, not built from pin type
data) -- color only applies to the template-based renderers below.
"""

from __future__ import annotations
import shutil
from .schema import Package, Pin
from .color import ColorMode, colorize_pin


def render(pkg: Package, part_name: str = "", mode: ColorMode = "off") -> str:
    """render a package to an ascii diagram string."""
    if pkg.ascii:
        return pkg.ascii
    t = pkg.template
    if t in ("dip", "soic", "ssop", "tssop"):
        return _render_dip(pkg, part_name, mode)
    if t in ("sip",):
        return _render_sip(pkg, part_name, mode)
    if t in ("sot23",):
        return _render_sot23(pkg, mode)
    if t in ("sot23-5", "sot23-6"):
        return _render_sot23_5(pkg, mode)
    if t in ("to92",):
        return _render_to92(pkg, mode)
    if t in ("to220", "to247"):
        return _render_to220(pkg, mode)
    if t in ("qfp", "lqfp", "tqfp", "qfn"):
        return _render_qfp(pkg, part_name, mode)
    if t in ("module",):
        return _render_module(pkg, part_name, mode)
    return _render_generic(pkg, part_name, mode)


def _pin_by_num(pkg: Package, n: int | str) -> Pin | None:
    for p in pkg.pins:
        if p.pin == n:
            return p
    return None


def _plain(p: Pin | None) -> str:
    return p.name if p else "?"


def _cname(p: Pin | None, mode: ColorMode, width: int = 0, align: str = ">") -> str:
    """pin name, padded to width BEFORE coloring.

    ANSI escape codes are invisible on screen but count toward str length, so
    padding/centering a colored string with an f-string width spec produces
    the wrong visual result. Always pad the plain text first, then wrap it.
    """
    text = _plain(p)
    if width:
        if align == "^":
            text = text.center(width)
        elif align == "<":
            text = text.ljust(width)
        else:
            text = text.rjust(width)
    if p is None:
        return text
    return colorize_pin(text, p.type, mode)


def _render_dip(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """dual inline package -- even pin count only. an odd count here silently
    dropped one pin from the diagram until this check existed (found on a
    module template used for a physically single-row part -- see sip
    instead for anything with pins along one edge, not split across two)."""
    n = pkg.pin_count
    if n % 2 != 0:
        raise ValueError(
            f"{part_name}: dip/module template needs an even pin_count, got {n} -- "
            "a single-row part belongs on the sip template instead"
        )
    half = n // 2
    # left column: pins 1..half (top to bottom)
    # right column: pins n..half+1 (top to bottom)
    left  = [_pin_by_num(pkg, i)       for i in range(1, half + 1)]
    right = [_pin_by_num(pkg, n - i)   for i in range(half)]

    lw = max((len(_plain(p)) for p in left),  default=3)
    nw = len(str(n))
    body_w = max(len(part_name), 10)

    lines = []
    lines.append(f"{'':>{lw+nw+2}}┌{'─'*body_w}┐")
    for i in range(half):
        lpin = left[i]
        rpin = right[i]
        lnum = i + 1
        rnum = n - i
        ln = _cname(lpin, mode, lw, ">")
        rn = _cname(rpin, mode)
        label = part_name if i == half // 2 else ""
        lines.append(
            f"{ln} -{lnum:>{nw}}┤{label:^{body_w}}├{rnum:<{nw}}- {rn}"
        )
    lines.append(f"{'':>{lw+nw+2}}└{'─'*body_w}┘")
    return "\n".join(lines)


def _render_sip(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """single inline package. number field width is set by the widest pin
    number so double-digit pins (10, 11, ...) still get a visible gap --
    a fixed width-2 field made them run together (e.g. "101112...")."""
    lines = [f"  {part_name}"]
    lines.append("  " + "┬" * pkg.pin_count)
    numw = max((len(str(p.pin)) for p in pkg.pins), default=1) + 1
    nums = "  " + "".join(f"{p.pin:<{numw}}" for p in pkg.pins)
    lines.append(nums)
    for p in pkg.pins:
        lines.append(f"  {p.pin}: {_cname(p, mode)}")
    return "\n".join(lines)


def _render_sot23(pkg: Package, mode: ColorMode = "off") -> str:
    """SOT-23 3-pin."""
    pins = {p.pin: p for p in pkg.pins}
    p1 = _cname(pins.get(1), mode)
    p2 = _cname(pins.get(2), mode)
    p3 = _cname(pins.get(3), mode)
    return (
        f"   {p1}  {p3}\n"
        f"    │    │\n"
        f"  ┌┴────┴┐\n"
        f"  │ SOT  │\n"
        f"  └──┬───┘\n"
        f"     │\n"
        f"    {p2}"
    )


def _render_sot23_5(pkg: Package, mode: ColorMode = "off") -> str:
    """SOT-23-5 or SOT-23-6."""
    pins = {p.pin: p for p in pkg.pins}
    top_pins = [pins.get(i) for i in range(1, pkg.pin_count // 2 + 1)]
    bot_pins = [pins.get(i) for i in range(pkg.pin_count, pkg.pin_count // 2, -1)]
    tw = max(len(_plain(p)) for p in top_pins + bot_pins)
    top = [_cname(p, mode, tw, "^") for p in top_pins]
    bot = [_cname(p, mode, tw, "^") for p in bot_pins]
    lines = []
    lines.append("  " + "  ".join(top))
    lines.append("  " + "┬  " * len(top))
    lines.append("  ┌" + "─" * (tw * len(top) + 2 * (len(top)-1)) + "┐")
    lines.append("  └" + "─" * (tw * len(top) + 2 * (len(top)-1)) + "┘")
    lines.append("  " + "┴  " * len(bot))
    lines.append("  " + "  ".join(bot))
    return "\n".join(lines)


def _render_to92(pkg: Package, mode: ColorMode = "off") -> str:
    pins = {p.pin: p for p in pkg.pins}
    p1 = _cname(pins.get(1), mode)
    p2 = _cname(pins.get(2), mode)
    p3 = _cname(pins.get(3), mode)
    return (
        f"    ╭───╮\n"
        f"    │   │   (flat face)\n"
        f"    ╰─┬─╯\n"
        f"   │  │  │\n"
        f"  {p1}  {p2}  {p3}"
    )


def _render_to220(pkg: Package, mode: ColorMode = "off") -> str:
    pins = {p.pin: p for p in pkg.pins}
    names = [_cname(pins.get(i), mode, 3, "^") for i in range(1, pkg.pin_count + 1)]
    return (
        "    ┌────────┐\n"
        "    │  TAB   │\n"
        "    └─┬──┬──┬┘\n"
        "      │  │  │\n"
        "    " + "  ".join(names)
    )


def _two_column_box(left: list[Pin | None], right: list[Pin | None],
                    label: str, mode: ColorMode = "off") -> str:
    """a DIP-style box with an arbitrary pin on each row of the left and right
    columns, each tagged with its real pin number. the building block for the
    two-view QFP/QFN diagram, where horizontal names only read cleanly on the
    left/right edges -- so we rotate to bring every edge to a side in turn."""
    rows = max(len(left), len(right))
    lw = max((len(_plain(p)) for p in left if p), default=3)
    nw = max((len(str(p.pin)) for p in left + right if p), default=1)
    body_w = max(len(label), 10)
    out = [f"{'':>{lw+nw+2}}┌{'─'*body_w}┐"]
    for i in range(rows):
        lp = left[i] if i < len(left) else None
        rp = right[i] if i < len(right) else None
        ln = _cname(lp, mode, lw, ">")
        lnum = f"{lp.pin:>{nw}}" if lp else " " * nw
        rnum = f"{rp.pin:<{nw}}" if rp else " " * nw
        rn = _cname(rp, mode)
        mid = label if i == rows // 2 else ""
        out.append(f"{ln} -{lnum}┤{mid:^{body_w}}├{rnum}- {rn}")
    out.append(f"{'':>{lw+nw+2}}└{'─'*body_w}┘")
    return "\n".join(out)


def _qfp_quadrants(pkg: Package):
    n = pkg.pin_count
    side = n // 4
    by = {p.pin: p for p in pkg.pins}
    bottom = [by.get(i) for i in range(1, side + 1)]                 # L->R
    left   = [by.get(i) for i in range(side + 1, 2 * side + 1)]      # top->bottom
    top    = [by.get(i) for i in range(2 * side + 1, 3 * side + 1)]  # L->R
    right  = [by.get(i) for i in range(3 * side + 1, n + 1)]         # top->bottom
    return side, bottom, left, top, right


def _render_qfp_square(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """the true top-view: a square with pins on all four edges, top/bottom names
    spread horizontally over their pins. faithful to the package, but wide."""
    side, bottom, left, top, right = _qfp_quadrants(pkg)
    cw = max([3] + [len(_plain(p)) for p in top + bottom])   # top/bottom slot width
    lw = max([3] + [len(_plain(p)) for p in left])           # left name column
    nw = max(2, len(str(pkg.pin_count)))                     # number column
    gutter = lw + 2 + nw                                     # "<name> -<num>" then ┤
    interior = side * cw + (side - 1)                        # slots + separators
    pad = " " * (gutter + 1)

    def row(cells):     # cells already centered to cw, joined by one space
        return pad + " ".join(cells)

    def border(l, mid, r):
        buf = ["─"] * interior
        for k in range(side):
            c = k * (cw + 1) + (cw - 1) // 2   # match str.center's single-char slot
            buf[c] = mid
        return " " * gutter + l + "".join(buf) + r

    ticks = lambda pins: row([("│" if p else " ").center(cw) for p in pins])
    nums = lambda pins: row([(str(p.pin) if p else "").center(cw) for p in pins])
    names = lambda pins: row([_cname(p, mode, cw, "^") for p in pins])

    out = [names(top), nums(top), ticks(top), border("┌", "┬", "┐")]
    mid = side // 2
    for i in range(side):
        lp, rp = left[i], right[i]
        ln = _cname(lp, mode, lw, ">")
        lnum = f"{lp.pin:>{nw}}" if lp else " " * nw
        rnum = f"{rp.pin:<{nw}}" if rp else " " * nw
        label = part_name if i == mid else ""
        out.append(f"{ln} -{lnum}┤{label:^{interior}}├{rnum}- {_cname(rp, mode)}")
    out += [border("└", "┴", "┘"), ticks(bottom), nums(bottom), names(bottom)]
    return "\n".join(out)


def _render_qfp(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """four-sided package (QFP/QFN/LQFP). prefer the faithful square top-view when
    it fits the terminal; fall back to two 90°-rotated DIP views when it would be
    too wide (ascii can't rotate the top/bottom names, so a narrow square would
    have to stack them -- misleading)."""
    side, bottom, left, top, right = _qfp_quadrants(pkg)
    cw = max([3] + [len(_plain(p)) for p in top + bottom])
    lw = max([3] + [len(_plain(p)) for p in left])
    nw = max(2, len(str(pkg.pin_count)))
    square_w = (lw + 2 + nw) + 1 + (side * cw + side - 1) + 1 + (nw + 2 + cw)
    avail = shutil.get_terminal_size((100, 24)).columns
    if square_w <= avail:
        return _render_qfp_square(pkg, part_name, mode)
    # narrow fallback: two DIP views, every pin still named + numbered.
    v1 = _two_column_box(left, list(reversed(right)), part_name, mode)
    v2 = _two_column_box(bottom, top, part_name, mode)
    return (
        f"  left + right edges:\n{v1}\n\n"
        f"  top + bottom edges (chip turned 90°):\n{v2}"
    )


def _render_module(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """module/breakout board -- two column like DIP but labeled as module."""
    return _render_dip(pkg, part_name, mode)


def _render_generic(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """fallback: numbered list."""
    lines = [f"{part_name} ({pkg.template}, {pkg.pin_count}-pin)"]
    for p in pkg.pins:
        name = _cname(p, mode, 16, "<")
        lines.append(f"  {p.pin:>3}: {name} {p.type:<12} {p.description}")
    return "\n".join(lines)
