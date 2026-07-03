"""schema-level invariants that the rest of the codebase assumes hold."""

from partinfo.schema import Part, Specs


def _minimal_part(**overrides):
    data = dict(
        id="testpart",
        name="TESTPART",
        full_name="Test Part",
        manufacturers=["Acme"],
        category="other",
        tags=[],
        description="a part for tests",
        packages={},
    )
    data.update(overrides)
    return Part(**data)


def test_part_defaults():
    p = _minimal_part()
    assert p.verified is False
    assert p.human_reviewed is False
    assert p.source == "human"
    assert p.variants == []


def test_human_reviewed_is_independent_of_source():
    p = _minimal_part(source="claude", human_reviewed=True)
    assert p.source == "claude"
    assert p.human_reviewed is True


def test_rth_fields_accept_floats_and_default_to_none():
    s = Specs()
    assert s.rth_jc_cw is None
    assert s.rth_ja_cw is None
    s = Specs(rth_jc_cw=5.0, rth_ja_cw=62.5)
    assert s.rth_jc_cw == 5.0
    assert s.rth_ja_cw == 62.5


def test_specs_extra_defaults_to_empty_dict():
    assert Specs().extra == {}
