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
    if t in ("diode",):
        return _render_diode(pkg, part_name, mode)
    if t in ("sot23",):
        return _render_sot23(pkg, mode)
    if t in ("sot23-5", "sot23-6"):
        return _render_sot23_5(pkg, mode)
    if t in ("to92",):
        return _render_to92(pkg, part_name, mode)
    if t in ("to220", "to247"):
        return _render_to220(pkg, part_name, mode)
    if t in ("can", "to1", "to5", "to18", "to39", "to72"):
        return _render_can(pkg, part_name, mode)
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
    notch = list("─" * body_w)                 # pin-1 orientation notch, top center
    notch[body_w // 2] = "◡"
    lines.append(f"{'':>{lw+nw+2}}┌{''.join(notch)}┐")
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
    """single inline package / single-row header (breakout modules, SIP ICs): a
    numbered contact strip. pin names live in the numbered list printed below the
    diagram, so the strip itself carries only numbers -- kept compact and aligned.
    cell width follows the widest pin number so 10, 11, ... never run together."""
    pins = sorted(pkg.pins, key=lambda p: int(p.pin) if str(p.pin).isdigit() else 0)
    cw = max(2, max((len(str(p.pin)) for p in pins), default=2))
    top = "  ┌" + "┬".join("─" * cw for _ in pins) + "┐"
    bot = "  └" + "┴".join("─" * cw for _ in pins) + "┘"
    cells = [colorize_pin(str(p.pin).rjust(cw), p.type, mode) for p in pins]
    mid = "  │" + "│".join(cells) + "│"
    return "\n".join([top, mid, bot])


def _render_diode(pkg: Package, part_name: str = "", mode: ColorMode = "off") -> str:
    """2-lead diode: the schematic symbol with numbered leads. pin 1 is the anode
    (triangle), pin 2 is the cathode (the bar) -- the banded end of the body.
    names live in the numbered list below the diagram."""
    pins = {p.pin: p for p in pkg.pins}

    def num(k):
        p = pins.get(k) or pins.get(str(k))
        return colorize_pin(str(k), p.type, mode) if p else str(k)

    return (
        f"   {num(1)} ──>|── {num(2)}\n"
        f"   anode    cathode (band)"
    )


def _render_sot23(pkg: Package, mode: ColorMode = "off") -> str:
    """SOT-23 3-pin: leads 1,2 on one side, lead 3 alone opposite (TO-236).
    numbered; names live in the list below."""
    pins = {p.pin: p for p in pkg.pins}

    def num(k):
        p = pins.get(k) or pins.get(str(k))
        return colorize_pin(str(k), p.type, mode) if p else str(k)

    return (
        f"      {num(3)}\n"
        f"      │\n"
        f"   ┌──┴──┐\n"
        f"   │ SOT │\n"
        f"   └─┬─┬─┘\n"
        f"     │ │\n"
        f"     {num(1)} {num(2)}"
    )


def _render_sot23_5(pkg: Package, mode: ColorMode = "off") -> str:
    """SOT-23-5 / SOT-23-6: 3 leads along the bottom (1,2,3 L->R), the rest along
    the top (numbered down from the highest). numbered; names live in the list."""
    n = pkg.pin_count
    pins = {p.pin: p for p in pkg.pins}
    gap, left = 3, 3
    bcols = [left + 1 + i * gap for i in range(3)]          # bottom leads 1,2,3
    top = list(range(n, 3, -1))                             # 5 -> [5,4]; 6 -> [6,5,4]
    tcols = [bcols[0], bcols[2]] if len(top) == 2 else list(bcols)

    def num(k):
        p = pins.get(k) or pins.get(str(k))
        return colorize_pin(str(k), p.type, mode) if p else str(k)

    def numrow(cols, nums):
        s, cur = "", 0
        for c, k in zip(cols, nums):
            s += " " * (c - cur) + num(k)
            cur = c + len(str(k))
        return s

    def tickrow(cols, ch):
        r = []
        for c in cols:
            _put(r, c, ch)
        return "".join(r)

    bl, br = left, bcols[-1] + 1
    return "\n".join([
        numrow(tcols, top),
        tickrow(tcols, "┬"),
        " " * bl + "┌" + "─" * (br - bl - 1) + "┐",
        " " * bl + "└" + "─" * (br - bl - 1) + "┘",
        tickrow(bcols, "┴"),
        numrow(bcols, [1, 2, 3]),
    ])


def _put(buf: list, col: int, s: str) -> None:
    """place `s` at absolute column `col` in a char-list line, extending as needed.
    building diagrams into a buffer keeps every glyph on its intended column, so
    alignment is correct by construction rather than by counting spaces by hand."""
    while len(buf) < col + len(s):
        buf.append(" ")
    for i, ch in enumerate(s):
        buf[col + i] = ch


def _lead_columns(n: int, ileft: int, inner: int, gap: int = 2) -> list:
    """evenly spaced lead columns, centered under a body of the given width."""
    span = (n - 1) * gap
    start = ileft + (inner - span) // 2
    return [start + i * gap for i in range(n)]


def _append_leads(out: list, pkg: Package, taps: list, mode: ColorMode, lead: str = "│") -> None:
    """append the straight lead row + the numbered row. numbers are colored by pin
    type and placed by concatenation so ANSI codes never shift them off the leads --
    the numbers sit directly under the leads, which is what keeps the bottom aligned."""
    pins = {p.pin: p for p in pkg.pins}
    r = []
    for t in taps:
        _put(r, t, lead)
    out.append("".join(r))
    line, cur = "", 0
    for i, col in enumerate(taps):
        num = i + 1
        p = pins.get(num) or pins.get(str(num))
        txt = colorize_pin(str(num), p.type, mode) if p else str(num)
        line += " " * (col - cur) + txt
        cur = col + len(str(num))
    out.append(line)


def _render_to220(pkg: Package, part_name: str = "", mode: ColorMode = "off", margin: int = 3) -> str:
    """TO-220 / TO-247: a light metal heatsink tab with the mounting hole up top,
    the heavy-outlined black plastic body below, then straight leads. fixed width
    -- it grows only with the lead count (e.g. TO-220-5), never with the part name,
    which is printed in the header line above the diagram. safe glyphs only."""
    n = pkg.pin_count
    if n < 2:
        return _render_generic(pkg, part_name, mode)
    inner = max(9, (n - 1) * 2 + 4)
    ileft = margin + 1
    ctr = ileft + inner // 2
    taps = _lead_columns(n, ileft, inner)
    pad = " " * margin
    out = [pad + "┌" + "─" * inner + "┐"]
    r = [" "] * (ileft + inner + 1)                    # light metal tab + mounting hole
    _put(r, margin, "│")
    _put(r, ctr - 2, "(")
    _put(r, ctr, "o")
    _put(r, ctr + 2, ")")
    _put(r, ileft + inner, "│")
    out.append("".join(r))
    out.append(pad + "┢" + "━" * inner + "┪")          # tab -> heavy black-plastic body
    for _ in range(2):
        out.append(pad + "┃" + " " * inner + "┃")
    r = [" "] * (ileft + inner + 1)                    # heavy body bottom + lead taps
    _put(r, margin, "┗")
    _put(r, ileft + inner, "┛")
    for c in range(ileft, ileft + inner):
        _put(r, c, "━")
    for t in taps:
        _put(r, t, "┳")
    out.append("".join(r))
    _append_leads(out, pkg, taps, mode, lead="┃")
    return "\n".join(out)


def _render_to92(pkg: Package, part_name: str = "", mode: ColorMode = "off", margin: int = 3) -> str:
    """TO-92: the small black plastic body (heavy outline) with three straight leads."""
    if pkg.pin_count != 3:
        return _render_sip(pkg, part_name, mode)
    inner = 7
    ileft = margin + 1
    taps = _lead_columns(3, ileft, inner)
    pad = " " * margin
    out = [pad + "┏" + "━" * inner + "┓",
           pad + "┃" + " " * inner + "┃"]
    r = [" "] * (ileft + inner + 1)
    _put(r, margin, "┗")
    _put(r, ileft + inner, "┛")
    for c in range(ileft, ileft + inner):
        _put(r, c, "━")
    for t in taps:
        _put(r, t, "┳")
    out.append("".join(r))
    _append_leads(out, pkg, taps, mode, lead="┃")
    return "\n".join(out)


def _render_can(pkg: Package, part_name: str = "", mode: ColorMode = "off", margin: int = 3) -> str:
    """metal can (TO-1/TO-5/TO-18/TO-39): a rounded metal body (light outline) with
    three straight leads -- the round silhouette sets it apart from the boxes."""
    if pkg.pin_count != 3:
        return _render_sip(pkg, part_name, mode)
    inner = 7
    ileft = margin + 1
    taps = _lead_columns(3, ileft, inner)
    pad = " " * margin
    out = [pad + "╭" + "─" * inner + "╮",
           pad + "│" + " " * inner + "│",
           pad + "│" + " " * inner + "│"]
    r = [" "] * (ileft + inner + 1)
    _put(r, margin, "╰")
    _put(r, ileft + inner, "╯")
    for c in range(ileft, ileft + inner):
        _put(r, c, "─")
    for t in taps:
        _put(r, t, "┬")
    out.append("".join(r))
    _append_leads(out, pkg, taps, mode, lead="│")
    return "\n".join(out)


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

    def border(lc, mid, rc):
        buf = ["─"] * interior
        for k in range(side):
            c = k * (cw + 1) + (cw - 1) // 2   # match str.center's single-char slot
            buf[c] = mid
        return " " * gutter + lc + "".join(buf) + rc

    def ticks(pins):
        return row([("│" if p else " ").center(cw) for p in pins])

    def nums(pins):
        return row([(str(p.pin) if p else "").center(cw) for p in pins])

    def names(pins):
        return row([_cname(p, mode, cw, "^") for p in pins])

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
