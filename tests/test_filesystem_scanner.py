"""Filesystem scanner tests — SI-001 identity + RAC-002 explainability.

RAC-002 (draft-adopted 2026-10-20) is the target specification:
every identity decision emits a Section 7 history event; confidence
lives on claims, never on stars; a birth event carries no confidence;
evidence is structured data, not free text.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from darkshield import Star, Universe
from darkshield.scanners import (
    CONTINUITY_THRESHOLD,
    SCHEMA_VERSION,
    SCANNER_VERSION,
    scan_filesystem,
)

ENVELOPE = {
    "event_id", "event_type", "timestamp",
    "schema_version", "scanner_version", "observation_id",
}


def _tree(files: dict[str, bytes]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ds-scan-"))
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return root


def _stars(universe: Universe) -> list[Star]:
    return [n for n in universe.nodes if isinstance(n, Star)]


def _events(universe: Universe, event_type: str) -> list[dict]:
    return [h for h in universe.history if h.get("event_type") == event_type]


def test_scan_creates_galaxy_stars_and_evidence() -> None:
    root = _tree({"a.txt": b"alpha", "sub/b.txt": b"beta"})
    try:
        u = scan_filesystem(root)
        assert len(_stars(u)) == 2
        contains = [r for r in u.relationships if r.relation == "contains"]
        assert len(contains) == 2
        assert all(r.primary_evidence() is not None for r in contains)
        observations = _events(u, "observation")
        assert observations and observations[-1]["observed"] == 2
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_every_event_carries_the_section7_envelope() -> None:
    root = _tree({"a.txt": b"alpha"})
    try:
        u = scan_filesystem(root)
        assert u.history, "scanner must record its decisions"
        for entry in u.history:
            assert ENVELOPE <= set(entry), entry
            assert entry["schema_version"] == SCHEMA_VERSION
            assert entry["scanner_version"] == SCANNER_VERSION
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_birth_events_have_no_confidence() -> None:
    """RAC-002 Section 7.5: birth is an observation, not an inference."""
    root = _tree({"a.txt": b"alpha", "b.txt": b"beta"})
    try:
        u = scan_filesystem(root)
        births = _events(u, "star_birth")
        assert len(births) == 2
        assert all("confidence" not in b for b in births)
        assert {b["star_id"] for b in births} == {s.id for s in _stars(u)}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_rescan_preserves_identity() -> None:
    root = _tree({"a.txt": b"alpha", "b.txt": b"beta"})
    try:
        u = scan_filesystem(root)
        first = sorted(s.id for s in _stars(u))
        u = scan_filesystem(root, u)
        assert sorted(s.id for s in _stars(u)) == first
        assert len(_events(u, "star_birth")) == 2  # no new births
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_rename_is_a_claim_with_structured_evidence() -> None:
    root = _tree({"report.txt": b"quarterly numbers"})
    try:
        u = scan_filesystem(root)
        star_id = _stars(u)[0].id
        os.rename(root / "report.txt", root / "report-final.txt")
        u = scan_filesystem(root, u)
        stars = _stars(u)
        assert len(stars) == 1 and stars[0].id == star_id
        claims = _events(u, "continuity_claim")
        assert len(claims) == 1  # RAC-002-A: exactly one
        claim = claims[0]
        assert claim["star_id"] == star_id
        assert claim["confidence"] >= CONTINUITY_THRESHOLD
        kinds = {e["type"] for e in claim["evidence"]}
        assert "same_inode" in kinds
        assert all(
            set(e) == {"type", "value", "weight", "source"}
            for e in claim["evidence"]
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_modify_records_star_modified_with_and_without_hash() -> None:
    root = _tree({"notes.txt": b"version one"})
    try:
        u = scan_filesystem(root)
        star_id = _stars(u)[0].id
        (root / "notes.txt").write_bytes(b"version two, edited and longer")
        u = scan_filesystem(root, u)
        modified = _events(u, "star_modified")
        assert modified and modified[-1]["star_id"] == star_id
        assert "size_changed" in modified[-1]["changes"]
        # With hashing, the hash change is recorded too.
        (root / "notes.txt").write_bytes(b"version three")
        u = scan_filesystem(root, u, hash_files=True)
        u2 = scan_filesystem(root, u, hash_files=True)
        (root / "notes.txt").write_bytes(b"version four!")
        u2 = scan_filesystem(root, u2, hash_files=True)
        hashed = [
            m for m in _events(u2, "star_modified")
            if "hash_changed" in m["changes"]
        ]
        assert hashed and hashed[-1]["hash_before"] != hashed[-1]["hash_after"]
        assert _stars(u2)[0].id == star_id
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_departure_and_rediscovery() -> None:
    root = _tree({"gone.txt": b"temporary", "stay.txt": b"stays"})
    try:
        u = scan_filesystem(root)
        gone_id = next(s.id for s in _stars(u) if s.name == "gone.txt")
        os.remove(root / "gone.txt")
        u = scan_filesystem(root, u)
        departures = _events(u, "star_departure")
        assert departures and departures[-1]["star_id"] == gone_id
        assert "last_observed_at" in departures[-1]
        # The star is retained, never deleted.
        assert any(s.id == gone_id for s in _stars(u))
        # It returns: rediscovery, not silent continuity, not a new birth.
        (root / "gone.txt").write_bytes(b"temporary")
        u = scan_filesystem(root, u)
        rediscoveries = _events(u, "star_rediscovery")
        assert rediscoveries and rediscoveries[-1]["star_id"] == gone_id
        assert len(_stars(u)) == 2
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_copy_delete_with_hash_continues() -> None:
    root = _tree({"docs/report.txt": b"same content"})
    try:
        u = scan_filesystem(root, hash_files=True)
        star_id = _stars(u)[0].id
        (root / "archive").mkdir()
        shutil.copy(root / "docs" / "report.txt", root / "archive" / "report.txt")
        os.remove(root / "docs" / "report.txt")
        u = scan_filesystem(root, u, hash_files=True)
        assert len(_stars(u)) == 1 and _stars(u)[0].id == star_id
        claims = _events(u, "continuity_claim")
        assert claims and claims[-1]["confidence"] == 0.87
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_copy_delete_without_hash_stays_unresolved() -> None:
    root = _tree({"docs/report.txt": b"same content"})
    try:
        u = scan_filesystem(root)
        star_id = _stars(u)[0].id
        (root / "archive").mkdir()
        shutil.copy(root / "docs" / "report.txt", root / "archive" / "report.txt")
        os.remove(root / "docs" / "report.txt")
        u = scan_filesystem(root, u)
        stars = _stars(u)
        assert len(stars) == 2
        new_star = next(s for s in stars if s.id != star_id)
        unresolved = _events(u, "identity_unresolved")
        assert unresolved and unresolved[-1]["star_id"] == new_star.id
        assert unresolved[-1]["candidate_star_ids"] == [star_id]
        assert unresolved[-1]["confidence"] < CONTINUITY_THRESHOLD
        assert unresolved[-1]["evidence"]  # never empty (Section 7.4)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_skip_dirs_and_no_self_observation() -> None:
    root = _tree({
        "keep.txt": b"keep",
        ".git/config": b"git",
        "User Data/cookies": b"browser",
    })
    try:
        u = scan_filesystem(root)
        assert len(_stars(u)) == 1
        assert not [n for n in u.nodes if n.CLASS_TYPE == "pulsar"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_threshold_is_the_ruled_value() -> None:
    assert CONTINUITY_THRESHOLD == 0.85
