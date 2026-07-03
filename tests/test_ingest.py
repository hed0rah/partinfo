"""every part and reference file in the repo must actually ingest cleanly.
this is the one test that would have caught silent index gaps before the
fix to ingest()'s error handling -- keep it passing."""

from partinfo.db import ingest, _PARTS


def test_ingest_has_no_errors(tmp_path):
    count, errors = ingest(db=tmp_path / "test.db")
    assert errors == []
    assert count > 0


def test_ingest_count_matches_file_count(tmp_path):
    count, _ = ingest(db=tmp_path / "test.db")
    file_count = len(list(_PARTS.rglob("*.json")))
    assert count == file_count


def test_ingest_reports_a_broken_file(tmp_path):
    parts_dir = tmp_path / "parts" / "mosfet"
    parts_dir.mkdir(parents=True)
    (parts_dir / "broken.json").write_text('{"id": "broken", "name": "X"')  # truncated json

    count, errors = ingest(parts_dir=tmp_path / "parts", db=tmp_path / "test.db",
                            refs_dir=tmp_path / "norefs")
    assert count == 0
    assert len(errors) == 1
    assert "broken.json" in errors[0]
