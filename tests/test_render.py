"""render every real part in every color mode -- an ANSI escape code or a
malformed f-string in any renderer crashes real users, not just this test."""

import re

import pytest

from partinfo.db import all_ids, lookup
from partinfo.render import fmt_full, fmt_ascii, fmt_pins, fmt_specs

MODES = ("off", "semantic", "minimal", "mixed")


def _strip_ansi(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


@pytest.fixture(scope="module")
def part_ids():
    return all_ids()


@pytest.mark.parametrize("mode", MODES)
def test_every_part_renders_in_every_mode(part_ids, mode):
    for pid in part_ids:
        part = lookup(pid)
        fmt_full(part, mode)
        fmt_ascii(part, mode=mode)
        fmt_pins(part, mode=mode)
        fmt_specs(part)


def test_specs_does_not_duplicate_a_label_present_in_extra():
    part = lookup("irf520")
    out = fmt_specs(part)
    assert out.count("Rds(on)") == 1


def test_ansi_codes_do_not_break_pin_name_alignment():
    part = lookup("ne555")
    plain = fmt_ascii(part, mode="off")
    colored = fmt_ascii(part, mode="semantic")
    # same visible width per line once ANSI codes are stripped
    assert plain.splitlines() == [_strip_ansi(line) for line in colored.splitlines()]
