"""color mode resolution -- NO_COLOR and tty-detection are the two things
a script or CI pipe actually depends on."""

from partinfo.color import resolve_mode


class _FakeStream:
    def __init__(self, is_tty):
        self._is_tty = is_tty

    def isatty(self):
        return self._is_tty


def test_no_color_env_forces_off_even_for_explicit_mode(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert resolve_mode("semantic") == "off"
    assert resolve_mode("auto") == "off"


def test_auto_resolves_to_semantic_on_a_tty(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert resolve_mode("auto", stream=_FakeStream(True)) == "semantic"


def test_auto_resolves_to_off_when_piped(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert resolve_mode("auto", stream=_FakeStream(False)) == "off"


def test_explicit_mode_passes_through_on_a_real_terminal(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert resolve_mode("mixed", stream=_FakeStream(True)) == "mixed"
