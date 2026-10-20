"""DG-1 acceptance tests: root-scoped gravity generation.

DG-1 (adopted as draft 2026-10-20): the first certified gravity
sources. Generation is an explicit phase (Section 11), sources are
independently disableable, evidence is authoritative, and the root
boundary is absolute.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from darkshield import Star, Universe
from darkshield.gravity.generate import DG1_SOURCES, generate_root_gravity
from darkshield.scanners import scan_filesystem


def _tree(files: dict[str, bytes]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="ds-dg1-"))
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return root


def _pair_edges(u: Universe) -> list:
    stars = {n.id for n in u.nodes if isinstance(n, Star)}
    return [
        r for r in u.relationships
        if r.source in stars and r.target in stars and r.relation != "contains"
    ]


def _edge_between(u: Universe, a_name: str, b_name: str):
    ids = {n.name: n.id for n in u.nodes if isinstance(n, Star)}
    a, b = ids[a_name], ids[b_name]
    for rel in _pair_edges(u):
        if {rel.source, rel.target} == {a, b}:
            return rel
    return None


def test_dg1_a_same_directory() -> None:
    root = _tree({"a.txt": b"a", "b.txt": b"b", "c.md": b"c"})
    try:
        u = scan_filesystem(root)
        stats = generate_root_gravity(u, root)
        assert stats["created"] == 3  # full clique of three
        edge = _edge_between(u, "a.txt", "b.txt")
        assert edge is not None and edge.relation == "same_directory"
        assert any(e.source == "same_directory" for e in edge.evidence)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dg1_b_explainability_exposes_sources() -> None:
    root = _tree({"a.txt": b"a", "b.txt": b"b"})
    try:
        u = scan_filesystem(root)
        generate_root_gravity(u, root)
        edge = _edge_between(u, "a.txt", "b.txt")
        assert edge is not None
        explanation = u.explain_relationship(edge.id)
        assert explanation is not None
        # Same directory AND shared extension both contributed.
        assert "same_directory" in explanation.sources
        assert "shared_extension" in explanation.sources
        assert explanation.supports(explanation.gravity)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dg1_c_source_disablement() -> None:
    root = _tree({"a.txt": b"a", "b.txt": b"b", "c.md": b"c"})
    try:
        u = scan_filesystem(root)
        generate_root_gravity(u, root)
        # Disable same_directory; shared_extension keeps a-b alive.
        generate_root_gravity(u, root, sources=["shared_extension"])
        assert not [
            e for r in _pair_edges(u) for e in r.evidence
            if e.source == "same_directory"
        ]
        ab = _edge_between(u, "a.txt", "b.txt")
        assert ab is not None  # survives on extension evidence
        assert _edge_between(u, "a.txt", "c.md") is None  # dir-only: gone
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dg1_d_root_boundary() -> None:
    root_a = _tree({"x.txt": b"x", "y.txt": b"y"})
    root_b = _tree({"x.txt": b"x", "y.txt": b"y"})
    try:
        u = scan_filesystem(root_a)
        u = scan_filesystem(root_b, u)
        generate_root_gravity(u, root_a)
        b_ids = {
            n.id for n in u.nodes
            if isinstance(n, Star) and n.path.startswith(str(root_b))
        }
        assert not [
            r for r in _pair_edges(u)
            if r.source in b_ids or r.target in b_ids
        ]
    finally:
        shutil.rmtree(root_a, ignore_errors=True)
        shutil.rmtree(root_b, ignore_errors=True)


def test_dg1_e_lifecycle_preservation() -> None:
    root = _tree({"a.txt": b"a", "b.txt": b"b"})
    try:
        u = scan_filesystem(root)
        generate_root_gravity(u, root)
        edge = _edge_between(u, "a.txt", "b.txt")
        assert edge is not None
        edge_id = edge.id
        os.remove(root / "b.txt")
        u = scan_filesystem(root, u)
        generate_root_gravity(u, root)
        assert u.get_gravity(edge_id) is None
        kinds = [h.get("event_type") for h in u.history]
        assert "gravity_created" in kinds and "gravity_removed" in kinds
        removed = [
            h for h in u.history
            if h.get("event_type") == "gravity_removed"
            and h.get("gravity_id") == edge_id
        ]
        assert removed, "the biography survives the removal"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_shared_parent_and_stem_and_extension() -> None:
    root = _tree({
        "drafts/report.docx": b"1",
        "data/report-final.docx": b"2",
        "other/notes.txt": b"3",
    })
    try:
        u = scan_filesystem(root)
        generate_root_gravity(u, root)
        edge = _edge_between(u, "report.docx", "report-final.docx")
        assert edge is not None
        sources = {e.source for e in edge.evidence}
        assert "shared_parent_directory" in sources
        assert "shared_name_stem" in sources
        assert "shared_extension" in sources
        # Primary relation = strongest creating source (parent, here:
        # the pair is not in the same directory).
        assert edge.relation == "shared_parent_directory"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_generation_is_idempotent() -> None:
    root = _tree({"a.txt": b"a", "b.txt": b"b"})
    try:
        u = scan_filesystem(root)
        first = generate_root_gravity(u, root)
        events_after_first = len(u.history)
        second = generate_root_gravity(u, root)
        assert first["created"] == 1
        assert second["created"] == 0 and second["updated"] == 0
        assert len(u.history) == events_after_first
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_all_sources_registered() -> None:
    assert DG1_SOURCES == (
        "same_directory",
        "shared_parent_directory",
        "shared_name_stem",
        "shared_extension",
    )
