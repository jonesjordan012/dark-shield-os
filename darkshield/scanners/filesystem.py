"""Filesystem scanner v0.2: turns a real directory into universe evidence.

Implements SI-001 (Star Identity Ruling):
- Star IDs are minted (uuid4) at first observation; they are NEVER
  derived from path, hash, inode, or any other observable property.
- Observable properties are recorded as facts on the star.
- Continuity between scans is evaluated on a ladder of evidence:
  exact path (observed) > inode (strong, 0.95) > hash+size with a
  single candidate (moderate, 0.87) > name+size similarity (weak, 0.30).

Conforms to RAC-002 (Continuity Explainability Criterion, draft-adopted
2026-10-20) as the v0.2 target specification:
- Every identity decision emits a history event in the Section 7
  envelope: event_id, event_type, timestamp, schema_version,
  scanner_version, observation_id.
- Canonical vocabulary: star_birth, star_departure, star_rediscovery,
  star_modified, continuity_claim, identity_unresolved,
  continuity_rejected.
- Evidence is structured data ({type, value, weight, source}), never
  free text, so future scanners can reinterpret it without rewriting
  history.
- Confidence lives on claim events only. A birth event carries no
  confidence: birth is an observation, not an inference.
- One observation record per scan; every decision references it, so a
  future observer can traverse Observation -> Decision -> Evidence ->
  Star from history alone (R2.4).

Honest-claims boundary (the Chain): the scanner claims existence, path,
size, inode, and content hash (when computed). It does not claim access
patterns, co-observation, or intent. The scanner's own looking creates
no observation evidence about itself: no pulsar is minted for it.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..entities import Galaxy, Star
from ..gravity.evidence import Evidence
from ..relations import Relationship
from ..universe import Universe

#: RAC-002 Section 7: schema + scanner versions stamped on every event.
SCHEMA_VERSION = "1.0"
SCANNER_VERSION = "0.2.0"

#: SI-001 Refinement 3: continuity is accepted at or above this
#: confidence. An implementation parameter of this scanner, not doctrine.
CONTINUITY_THRESHOLD = 0.85

CONF_INODE = 0.95  # strong: stable file identifier, new path
CONF_HASH = 0.87  # moderate: hash+size, exactly one candidate
CONF_WEAK = 0.30  # weak: same name + size at a new path
CONF_REJECT = 0.90  # confidence in a rejection (inode contradicted by hash)

#: Directories the scanner does not enter (app internals, VCS, caches).
SKIP_DIRS = frozenset({
    ".git",
    "__pycache__",
    "node_modules",
    "User Data",
    "AppData",
    "$Recycle.Bin",
    "System Volume Information",
})

_PRESENCE_EVENTS = {"star_birth", "star_departure", "star_rediscovery"}


def _mint(prefix: str) -> str:
    return f"{prefix}:{uuid4().hex}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _evidence(kind: str, value: bool, weight: float) -> dict:
    """Structured evidence entry (RAC-002 Section 7.7)."""
    return {"type": kind, "value": value, "weight": weight, "source": "filesystem"}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _observe(root: Path, hash_files: bool) -> list[dict]:
    """Walk the root and return one observation dict per file."""
    observations: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            try:
                stat = path.stat()
            except OSError:
                continue
            observations.append({
                "path": str(path),
                "name": filename,
                "size": stat.st_size,
                "inode": stat.st_ino or None,
                "sha256": _hash_file(path) if hash_files else None,
            })
    return observations


def _departed_star_ids(universe: Universe) -> set[str]:
    """Stars whose latest presence event is a departure.

    Derived from history each scan (RAC-002: no decision may exist
    solely as scanner state). Legacy v0.1 'not_observed' events count
    as departures for this derivation.
    """
    last_presence: dict[str, str] = {}
    for entry in universe.history:
        event_type = entry.get("event_type") or entry.get("event")
        star_id = entry.get("star_id") or entry.get("entity_id")
        if star_id is None:
            continue
        if event_type in _PRESENCE_EVENTS:
            last_presence[star_id] = event_type
        elif event_type == "not_observed":
            last_presence[star_id] = "star_departure"
    return {sid for sid, ev in last_presence.items() if ev == "star_departure"}


def scan_filesystem(
    root: str | Path,
    universe: Universe | None = None,
    *,
    hash_files: bool = False,
) -> Universe:
    """Scan a directory tree into a universe, per SI-001 + RAC-002.

    The root becomes (or reuses) a directory galaxy; files become
    stars contained by it, with filesystem evidence on each
    containment relationship. Re-scanning the same root continues
    existing stars whenever the continuity ladder supports it, and
    records every identity decision as a RAC-002 history event.
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"scan root is not a directory: {root_path}")
    if universe is None:
        universe = Universe(universe_id=f"urn:darkshield:universe:{uuid4().hex[:12]}")

    observation_id = _mint("obs")
    stats = {
        "observed": 0, "new": 0, "claims": 0, "unresolved": 0,
        "rejected": 0, "departed": 0, "rediscovered": 0, "modified": 0,
    }

    def emit(event_type: str, star_id: str | None = None, **fields: object) -> dict:
        """Append a RAC-002 Section 7 event to universe history."""
        entry: dict = {
            "event_id": _mint("evt"),
            "event_type": event_type,
            "timestamp": _now().isoformat(),
            "schema_version": SCHEMA_VERSION,
            "scanner_version": SCANNER_VERSION,
            "observation_id": observation_id,
        }
        if star_id is not None:
            entry["star_id"] = star_id
        entry.update(fields)
        universe.history.append(entry)
        return entry

    roots = universe.meta.setdefault("roots", {})
    root_key = str(root_path)
    galaxy_id = roots.get(root_key)
    galaxy = None
    if galaxy_id:
        galaxy = next(
            (n for n in universe.nodes if n.id == galaxy_id and isinstance(n, Galaxy)),
            None,
        )
    if galaxy is None:
        galaxy = Galaxy(id=_mint("galaxy"), name=root_key, kind="directory")
        universe.add_galaxy(galaxy)
        roots[root_key] = galaxy.id

    prefix = root_key + os.sep
    priors = [
        n for n in universe.nodes
        if isinstance(n, Star) and (n.path == root_key or n.path.startswith(prefix))
    ]
    by_path = {s.path: s for s in priors}
    unmatched: dict[str, Star] = {s.id: s for s in priors}
    departed = _departed_star_ids(universe)
    observations = _observe(root_path, hash_files)
    stats["observed"] = len(observations)

    def contain(star: Star) -> None:
        evidence = Evidence(
            source="filesystem",
            observations=1,
            confidence=1.0,
            details=f"observed at {star.path} during filesystem scan",
        )
        existing = universe.find_relationship(galaxy.id, star.id)
        if existing is not None and existing.relation == "contains":
            existing.attach_evidence(evidence)
        else:
            universe.add_relationship(Relationship(
                id=_mint("rel"),
                source=galaxy.id,
                target=star.id,
                relation="contains",
                evidence=[evidence],
            ))

    def note_return(star: Star) -> None:
        if star.id in departed:
            emit("star_rediscovery", star.id, path=star.path)
            stats["rediscovered"] += 1
            departed.discard(star.id)

    def apply_facts(star: Star, obs: dict) -> None:
        star.path = obs["path"]
        star.name = obs["name"]
        star.size_bytes = obs["size"]
        if obs["inode"] is not None:
            star.inode = obs["inode"]
        if obs["sha256"] is not None:
            star.sha256 = obs["sha256"]
        star.updated_at = _now()
        contain(star)

    def note_modified(star: Star, obs: dict) -> None:
        changes: list[str] = []
        fields: dict = {}
        if star.size_bytes != obs["size"]:
            changes.append("size_changed")
            fields["size_before"] = star.size_bytes
            fields["size_after"] = obs["size"]
        if star.sha256 and obs["sha256"] and star.sha256 != obs["sha256"]:
            changes.append("hash_changed")
            fields["hash_before"] = star.sha256
            fields["hash_after"] = obs["sha256"]
        if changes:
            emit("star_modified", star.id, changes=changes, **fields)
            stats["modified"] += 1

    def claim(star: Star, obs: dict, confidence: float, evidence: list[dict]) -> None:
        emit(
            "continuity_claim", star.id,
            prior_path=star.path,
            observed_path=obs["path"],
            confidence=confidence,
            evidence=evidence,
        )
        stats["claims"] += 1
        note_modified(star, obs)
        apply_facts(star, obs)
        note_return(star)

    def mint_star(obs: dict) -> Star:
        star = Star(
            id=_mint("star"),
            name=obs["name"],
            path=obs["path"],
            size_bytes=obs["size"],
            sha256=obs["sha256"],
            inode=obs["inode"],
        )
        universe.add_star(star)
        stats["new"] += 1
        # RAC-002 Section 7.5: a birth event carries NO confidence.
        emit("star_birth", star.id, path=obs["path"])
        contain(star)
        return star

    # Pass 1: exact path — observed continuity, no claim needed.
    remaining: list[dict] = []
    for obs in observations:
        star = by_path.get(obs["path"])
        if star is not None and star.id in unmatched:
            note_modified(star, obs)
            apply_facts(star, obs)
            note_return(star)
            del unmatched[star.id]
        else:
            remaining.append(obs)

    # Pass 2: inode — strong evidence of a move, unless the content
    # hash contradicts it (an inode reused by a different file):
    # then the continuation is rejected, on the record.
    still: list[dict] = []
    for obs in remaining:
        match = None
        if obs["inode"] is not None:
            for candidate in unmatched.values():
                if candidate.inode is not None and candidate.inode == obs["inode"]:
                    match = candidate
                    break
        if match is None:
            still.append(obs)
            continue
        if (
            obs["sha256"] and match.sha256 and obs["sha256"] != match.sha256
        ):
            star = mint_star(obs)
            emit(
                "continuity_rejected", star.id,
                candidate_star_ids=[match.id],
                confidence=CONF_REJECT,
                evidence=[
                    _evidence("same_inode", True, CONF_INODE),
                    _evidence("same_hash", False, 0.80),
                ],
                reason="inode matched but content hash contradicts; "
                       "treated as inode reuse, not continuity",
            )
            stats["rejected"] += 1
            continue
        if CONF_INODE >= CONTINUITY_THRESHOLD:
            evidence = [_evidence("same_inode", True, CONF_INODE)]
            if match.size_bytes == obs["size"]:
                evidence.append(_evidence("same_size", True, 0.40))
            claim(match, obs, CONF_INODE, evidence)
            del unmatched[match.id]
        else:
            still.append(obs)
    remaining = still

    # Pass 3: hash — moderate with a single candidate; ambiguous otherwise.
    still = []
    for obs in remaining:
        candidates = []
        if obs["sha256"]:
            candidates = [
                s for s in unmatched.values() if s.sha256 == obs["sha256"]
            ]
        if len(candidates) == 1 and CONF_HASH >= CONTINUITY_THRESHOLD:
            claim(
                candidates[0], obs, CONF_HASH,
                [
                    _evidence("same_hash", True, 0.80),
                    _evidence("same_size", True, 0.40),
                ],
            )
            del unmatched[candidates[0].id]
        elif len(candidates) > 1:
            star = mint_star(obs)
            emit(
                "identity_unresolved", star.id,
                candidate_star_ids=sorted(s.id for s in candidates),
                confidence=CONF_HASH,
                evidence=[
                    _evidence("same_hash", True, 0.80),
                    _evidence("same_size", True, 0.40),
                ],
                reason="multiple viable continuations; SI-001 forbids a guess",
            )
            stats["unresolved"] += 1
        else:
            still.append(obs)
    remaining = still

    # Pass 4: weak similarity — recorded unresolved, never claimed.
    for obs in remaining:
        weak = [
            s for s in unmatched.values()
            if s.name == obs["name"] and s.size_bytes == obs["size"]
        ]
        star = mint_star(obs)
        if weak:
            emit(
                "identity_unresolved", star.id,
                candidate_star_ids=sorted(s.id for s in weak),
                confidence=CONF_WEAK,
                evidence=[
                    _evidence("same_name", True, 0.20),
                    _evidence("same_size", True, 0.40),
                ],
                reason="weak evidence below CONTINUITY_THRESHOLD",
            )
            stats["unresolved"] += 1

    # Priors not observed this scan: departed, retained, never deleted.
    for star in unmatched.values():
        if star.id not in departed:
            emit(
                "star_departure", star.id,
                last_observed_at=star.updated_at.isoformat(),
                path=star.path,
            )
            stats["departed"] += 1

    # The observation record itself (RAC-002 Section 7.8): one per scan,
    # referenced by every decision emitted above.
    emit(
        "observation", None,
        root=root_key,
        hashed=hash_files,
        **stats,
    )
    universe.snapshot_at = _now()
    return universe
