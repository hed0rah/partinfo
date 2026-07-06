"""
ANSI color support for partinfo output.
no dependency -- raw escape codes, degrades to plain text in every non-terminal
context. see docs/superpowers/specs/2026-07-02-colored-rendering-design.md.
"""

from __future__ import annotations
import os
import sys
from typing import Literal

ColorMode = Literal["auto", "semantic", "minimal", "mixed", "off"]

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

# base 8 ANSI colors + bright variants only, for maximum terminal compatibility.
# red is reserved for warnings; never used for a pin type.
_PIN_COLORS: dict[str, str] = {
    "power": "\033[93m",          # bright yellow
    "ground": "\033[90m",         # bright black / gray
    "input": "\033[34m",          # blue
    "output": "\033[32m",         # green
    "bidirectional": "\033[36m",  # cyan
    "passive": "",                # uncolored / default
    "analog": "\033[35m",         # magenta
    "clock": "\033[94m",          # bright blue
    "reset": "\033[95m",          # bright magenta
    "nc": _DIM,                   # faint, de-emphasized
}

_WARN_MILD = "\033[33m"          # orange-ish (standard yellow)
_WARN_LOUD = _BOLD + "\033[91m"  # bold bright red
_SECTION = "\033[35m"            # magenta, matches existing header punctuation


def resolve_mode(mode: ColorMode, stream=None) -> ColorMode:
    """turn 'auto' (and NO_COLOR) into a concrete mode. stream defaults to stdout."""
    if os.environ.get("NO_COLOR") is not None:
        return "off"
    if mode != "auto":
        return mode
    stream = stream if stream is not None else sys.stdout
    return "semantic" if getattr(stream, "isatty", lambda: False)() else "off"


def colorize_pin(text: str, pin_type: str, mode: ColorMode) -> str:
    """color a pin name by its function. only semantic and mixed modes color pins."""
    if mode not in ("semantic", "mixed"):
        return text
    code = _PIN_COLORS.get(pin_type, "")
    if not code:
        return text
    return f"{code}{text}{_RESET}"


def colorize_warning(text: str, mode: ColorMode) -> str:
    """color a trust/provenance warning. minimal = muted, mixed = loud, else plain."""
    if mode == "minimal":
        return f"{_WARN_MILD}{text}{_RESET}"
    if mode == "mixed":
        return f"{_WARN_LOUD}{text}{_RESET}"
    return text


def colorize_section(text: str, mode: ColorMode) -> str:
    """color a section header. every non-off mode gets this, it's a low-risk aid."""
    if mode == "off":
        return text
    return f"{_SECTION}{text}{_RESET}"


def colorize_dim(text: str, mode: ColorMode) -> str:
    """de-emphasize secondary text (table headers/rules, spec labels). low-risk,
    so every non-off mode gets it, matching colorize_section's philosophy."""
    if mode == "off":
        return text
    return f"{_DIM}{text}{_RESET}"
