"""
SQLite index over the bundled parts/ and references/ JSON directories.
rebuild with: partinfo ingest
"""

from __future__ import annotations
import json
import os
import re
import sqlite3
import sys
from importlib import resources
from pathlib import Path
from . import __version__
from .schema import Part, RefEntry, Connector

# parts/ and references/ ship inside the package (src/partinfo/data/) so they're
# read-only bundled data, found the same way whether this is an editable dev
# checkout or a real pip/pipx install -- never write into this location.
_DATA = resources.files(__package__) / "data"
_PARTS = _DATA / "parts"
_REFS = _DATA / "references"
_CONNS = _DATA / "connectors"

# the SQLite index is a derived, writable cache -- it does not belong inside
# the installed package. XDG_DATA_HOME (default ~/.local/share) is standard
# on Linux; override with the env var if you want it somewhere else.
_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
_DB = _DATA_HOME / "partinfo" / "parts.db"


def _conn(db: Path = _DB) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE IF NOT EXISTS parts (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL,
            tags        TEXT NOT NULL,   -- JSON array
            description TEXT NOT NULL,
            aliases     TEXT NOT NULL,   -- JSON array
            blob        TEXT NOT NULL,   -- full JSON
            source      TEXT NOT NULL DEFAULT 'human'
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS parts_fts USING fts5(
            id, name, aliases, tags, description,
            content=parts, content_rowid=rowid
        );
        CREATE TABLE IF NOT EXISTS refs (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            topic       TEXT NOT NULL,
            tags        TEXT NOT NULL,   -- JSON array
            summary     TEXT NOT NULL,
            body        TEXT NOT NULL DEFAULT '',
            blob        TEXT NOT NULL,   -- full JSON
            source      TEXT NOT NULL DEFAULT 'human'
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS refs_fts USING fts5(
            id, title, tags, summary, body,
            content=refs, content_rowid=rowid
        );
        CREATE TABLE IF NOT EXISTS connectors (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            standard    TEXT NOT NULL DEFAULT '',
            tags        TEXT NOT NULL,   -- JSON array
            description TEXT NOT NULL,
            aliases     TEXT NOT NULL,   -- JSON array
            blob        TEXT NOT NULL,   -- full JSON
            source      TEXT NOT NULL DEFAULT 'human'
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS connectors_fts USING fts5(
            id, name, aliases, tags, description,
            content=connectors, content_rowid=rowid
        );
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    return c


def _ensure_index(db: Path = _DB) -> None:
    """build the index into db on first use, and rebuild it if the installed
    package version has changed since it was built -- otherwise `pip install
    -U partinfo` keeps serving the previous version's data (new/changed parts
    invisible) until someone thinks to run `partinfo ingest` manually. safe to
    call on every read; a no-op once the index matches the current version."""
    conn = _conn(db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        row = conn.execute("SELECT value FROM meta WHERE key='version'").fetchone()
        indexed_version = row[0] if row else None
    finally:
        conn.close()
    if count == 0:
        print("partinfo: building local index (first run)...", file=sys.stderr)
        ingest(db=db)
    elif indexed_version != __version__:
        print(f"partinfo: rebuilding local index ({indexed_version} -> {__version__})...",
              file=sys.stderr)
        ingest(db=db)


def ingest(parts_dir: Path = _PARTS, db: Path = _DB,
           refs_dir: Path = _REFS) -> tuple[int, list[str]]:
    """scan parts/ and references/, rebuild parts.db.
    returns (part count, list of "filename: error" strings for any file
    that failed to parse or validate -- a non-empty list means the index
    is missing entries, not just a cosmetic warning)."""
    conn = _conn(db)
    conn.execute("DELETE FROM parts")
    conn.execute("DELETE FROM parts_fts")
    count = 0
    errors = []
    for f in sorted(parts_dir.rglob("*.json")):
        try:
            data = json.loads(f.read_text())
            part = Part(**data)
            conn.execute(
                "INSERT OR REPLACE INTO parts VALUES (?,?,?,?,?,?,?,?)",
                (
                    part.id,
                    part.name,
                    part.category,
                    json.dumps(part.tags),
                    part.description,
                    json.dumps(part.aliases),
                    f.read_text(),
                    part.source,
                )
            )
            count += 1
        except Exception as e:
            errors.append(f"{f.relative_to(parts_dir.parent)}: {e}")
    conn.execute("INSERT INTO parts_fts(parts_fts) VALUES ('rebuild')")
    ref_count, ref_errors = ingest_refs(conn, refs_dir)
    errors.extend(ref_errors)
    conn_count, conn_errors = ingest_connectors(conn, _CONNS)
    errors.extend(conn_errors)
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('version', ?)", (__version__,))
    conn.commit()
    return count, errors


def ingest_refs(conn: sqlite3.Connection, refs_dir: Path = _REFS) -> tuple[int, list[str]]:
    """scan references/, rebuild the refs tables. returns (ref count, errors)."""
    conn.execute("DELETE FROM refs")
    conn.execute("DELETE FROM refs_fts")
    count = 0
    errors = []
    if refs_dir.exists():
        for f in sorted(refs_dir.rglob("*.json")):
            try:
                ref = RefEntry(**json.loads(f.read_text()))
                conn.execute(
                    "INSERT OR REPLACE INTO refs VALUES (?,?,?,?,?,?,?,?)",
                    (
                        ref.id,
                        ref.title,
                        ref.topic,
                        json.dumps(ref.tags),
                        ref.summary,
                        ref.body or "",
                        f.read_text(),
                        ref.source,
                    )
                )
                count += 1
            except Exception as e:
                errors.append(f"{f.relative_to(refs_dir.parent)}: {e}")
    conn.execute("INSERT INTO refs_fts(refs_fts) VALUES ('rebuild')")
    return count, errors


def ingest_connectors(conn: sqlite3.Connection, conns_dir: Path = _CONNS) -> tuple[int, list[str]]:
    """scan connectors/, rebuild the connectors tables. returns (count, errors)."""
    conn.execute("DELETE FROM connectors")
    conn.execute("DELETE FROM connectors_fts")
    count = 0
    errors = []
    if conns_dir.exists():
        for f in sorted(conns_dir.rglob("*.json")):
            try:
                c = Connector(**json.loads(f.read_text()))
                conn.execute(
                    "INSERT OR REPLACE INTO connectors VALUES (?,?,?,?,?,?,?,?)",
                    (
                        c.id,
                        c.name,
                        c.standard or "",
                        json.dumps(c.tags),
                        c.description,
                        json.dumps(c.aliases),
                        f.read_text(),
                        c.source,
                    )
                )
                count += 1
            except Exception as e:
                errors.append(f"{f.relative_to(conns_dir.parent)}: {e}")
    conn.execute("INSERT INTO connectors_fts(connectors_fts) VALUES ('rebuild')")
    return count, errors


def lookup(query: str, db: Path = _DB) -> Part | None:
    """exact match: id, name, or alias."""
    _ensure_index(db)
    conn = _conn(db)
    q = query.strip().lower()
    row = conn.execute("SELECT blob FROM parts WHERE id=? OR lower(name)=?", (q, q)).fetchone()
    if not row:
        # check aliases, then variant mpns (so "p2n2222a" resolves to "2n2222")
        for r in conn.execute("SELECT blob, aliases FROM parts").fetchall():
            aliases = json.loads(r["aliases"])
            if q in [a.lower() for a in aliases]:
                row = r
                break
            blob = json.loads(r["blob"])
            if q in [v.get("mpn", "").lower() for v in blob.get("variants", [])]:
                row = r
                break
    if row:
        return Part(**json.loads(row["blob"]))
    return None


def _fts_query(query: str) -> str | None:
    """turn a free-text query into a safe FTS5 MATCH expression.

    the default fts5 tokenizer treats -, /, :, *, ", etc. as query syntax, so a
    natural query like "h-bridge" or "i/o expander" raises a parse error. split
    the input into bare word tokens and quote each as a string literal, so every
    term is matched verbatim and all terms are required (implicit AND). returns
    None when the query has no searchable tokens.
    """
    tokens = re.findall(r"\w+", query)
    if not tokens:
        return None
    return " ".join(f'"{t}"' for t in tokens)


def search(query: str, limit: int = 10, db: Path = _DB) -> list[Part]:
    """full-text search across name, tags, description, aliases."""
    _ensure_index(db)
    match = _fts_query(query)
    if match is None:
        return []
    conn = _conn(db)
    rows = conn.execute(
        """
        SELECT p.blob FROM parts p
        JOIN parts_fts f ON p.rowid = f.rowid
        WHERE parts_fts MATCH ?
        ORDER BY rank LIMIT ?
        """,
        (match, limit),
    ).fetchall()
    return [Part(**json.loads(r["blob"])) for r in rows]


def all_ids(db: Path = _DB) -> list[str]:
    _ensure_index(db)
    conn = _conn(db)
    return [r[0] for r in conn.execute("SELECT id FROM parts ORDER BY id").fetchall()]


def ref_lookup(query: str, db: Path = _DB) -> RefEntry | None:
    """exact match on a reference id or title."""
    _ensure_index(db)
    conn = _conn(db)
    q = query.strip().lower()
    row = conn.execute(
        "SELECT blob FROM refs WHERE id=? OR lower(title)=?", (q, q)
    ).fetchone()
    if row:
        return RefEntry(**json.loads(row["blob"]))
    return None


def ref_search(query: str, limit: int = 10, db: Path = _DB) -> list[RefEntry]:
    """full-text search across reference title, tags, summary, body."""
    _ensure_index(db)
    match = _fts_query(query)
    if match is None:
        return []
    conn = _conn(db)
    rows = conn.execute(
        """
        SELECT r.blob FROM refs r
        JOIN refs_fts f ON r.rowid = f.rowid
        WHERE refs_fts MATCH ?
        ORDER BY rank LIMIT ?
        """,
        (match, limit),
    ).fetchall()
    return [RefEntry(**json.loads(r["blob"])) for r in rows]


def ref_all_ids(db: Path = _DB) -> list[str]:
    _ensure_index(db)
    conn = _conn(db)
    return [r[0] for r in conn.execute("SELECT id FROM refs ORDER BY id").fetchall()]


def conn_lookup(query: str, db: Path = _DB) -> Connector | None:
    """exact match on a connector id, name, or alias."""
    _ensure_index(db)
    conn = _conn(db)
    q = query.strip().lower()
    row = conn.execute(
        "SELECT blob FROM connectors WHERE id=? OR lower(name)=?", (q, q)
    ).fetchone()
    if not row:
        for r in conn.execute("SELECT blob, aliases FROM connectors").fetchall():
            if q in [a.lower() for a in json.loads(r["aliases"])]:
                row = r
                break
    if row:
        return Connector(**json.loads(row["blob"]))
    return None


def conn_search(query: str, limit: int = 10, db: Path = _DB) -> list[Connector]:
    """full-text search across connector name, tags, description, aliases."""
    _ensure_index(db)
    match = _fts_query(query)
    if match is None:
        return []
    conn = _conn(db)
    rows = conn.execute(
        """
        SELECT c.blob FROM connectors c
        JOIN connectors_fts f ON c.rowid = f.rowid
        WHERE connectors_fts MATCH ?
        ORDER BY rank LIMIT ?
        """,
        (match, limit),
    ).fetchall()
    return [Connector(**json.loads(r["blob"])) for r in rows]


def conn_all_ids(db: Path = _DB) -> list[str]:
    _ensure_index(db)
    conn = _conn(db)
    return [r[0] for r in conn.execute("SELECT id FROM connectors ORDER BY id").fetchall()]
