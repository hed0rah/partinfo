"""
ascii package diagram renderer.
given a Package, draws a human-readable pinout diagram.
pre-rendered ascii stored in package.ascii takes priority -- renderer is
the fallback for packages without a stored diagram. pre-rendered diagrams
are never colored (they're free-form strings, not built from pin type
data) -- color only applies to the template-based renderers below.
"""

from __future__ import annotations
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
    """dual inline package -- any even pin count."""
    n = pkg.pin_count
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
    """single inline package."""
    lines = [f"  {part_name}"]
    lines.append("  " + "┬" * pkg.pin_count)
    nums = "  " + "".join(f"{p.pin:<2}" if isinstance(p.pin, int) else f"{p.pin:<2}" for p in pkg.pins)
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


def _render_qfp(pkg: Package, part_name: str, mode: ColorMode = "off") -> str:
    """four-sided package -- QFP/QFN/LQFP."""
    n = pkg.pin_count
    side = n // 4
    by_num = {p.pin: p for p in pkg.pins}

    bottom_p = [by_num.get(i) for i in range(1, side + 1)]
    left_p   = [by_num.get(i) for i in range(side + 1, 2 * side + 1)]
    top_p    = [by_num.get(i) for i in range(2 * side + 1, 3 * side + 1)]
    right_p  = [by_num.get(i) for i in range(3 * side + 1, n + 1)]

    pw = max(len(_plain(p)) for p in bottom_p + left_p + top_p + right_p)
    inner_w = max(len(part_name) + 4, (pw + 2) * side)

    bottom_pins = [_cname(p, mode, inner_w, "^") for p in bottom_p]
    left_pins   = [_cname(p, mode, pw, ">") for p in left_p]
    top_pins    = [_cname(p, mode, inner_w, "^") for p in top_p]
    right_pins  = [_cname(p, mode) for p in right_p]

    lines = []
    # top pins (above body)
    for p in reversed(top_pins):
        lines.append(f"  {' ' * pw}  {p}")
    lines.append(f"  {' ' * pw}  ┌{'─' * inner_w}┐")
    # left + right side rows
    mid = side // 2
    for i in range(side):
        lp = left_pins[i]
        rp = right_pins[side - 1 - i]
        label = part_name if i == mid else ""
        lines.append(f"  {lp} ─┤{label:^{inner_w}}├─ {rp}")
    lines.append(f"  {' ' * pw}  └{'─' * inner_w}┘")
    # bottom pins
    for p in bottom_pins:
        lines.append(f"  {' ' * pw}  {p}")
    return "\n".join(lines)


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
