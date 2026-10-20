"""The Moonlight Reflector (ML-P1 Phase 1).

A Moon is created by reflecting a snapshot of a universe:

    Sun -> Snapshot -> Moon

The snapshot is constitutional evidence of origin. Reflection is a
continuity claim, not an identity merge (ML-001 Section 5.3): the
reflected star keeps its id, and its global identity is the pair
(universe_id, object_id) -- (sun, star:x) and (moon:y, star:x)
share ancestry; they are not the same object.

Isolation exists by construction (ML-P1 Section 5): the Moon is an
independent deserialized object graph. No mutable Sun object is
referenced by the Moon. Shared mutable state is a certification
failure, not a runtime concern.

The Reflector maintains an explicit Moon Registry (ML-P1 ruling,
Finding 2): a visible, serializable registry.json inside the store.
load_moon() resolves exclusively through the registry. There is no
hidden runtime registry.

Deletion refuses (ML-P1 ruling, Finding 3): delete_moon() fails
when no verified archive exists. The required order is:

    archive -> verify archive -> delete

Preservation is a visible act performed by an operator, never a
side effect silently produced by deletion.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..universe import Universe

REFLECTOR_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"

# ML-P1 ruling (Finding 1): the closed Phase-1 moon_type value set.
# Future values may be added only through constitutional revision.
MOON_TYPES = ("research", "development", "hallucination", "eclipse")

_PRODUCER = {"producer": "moonlight-reflector",
             "producer_version": REFLECTOR_VERSION}


class MoonlightError(RuntimeError):
    """A Moonlight constitutional or registry violation."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _mint(prefix: str) -> str:
    return f"{prefix}:{uuid4().hex}"


def _filename(identifier: str, suffix: str = ".json") -> str:
    """Map an id to a portable filename (colons are illegal in
    Windows filenames, so moon:/snap: ids are stored sanitized)."""
    return identifier.replace(":", "_").replace("/", "_") + suffix


def _state_hash(universe: Universe) -> str:
    """Fingerprint of a universe's state, excluding its history.

    Used to detect modification at store boundaries (ML-P1 audit
    Finding 5): moon_modified is emitted when a Moon is saved back
    through the Reflector with changed state -- honestly, at the
    moment the change becomes visible to the store.
    """
    data = universe.to_dict()
    state = {k: data[k] for k in ("universe_id", "meta", "nodes",
                                  "relationships")}
    blob = json.dumps(state, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class Reflector:
    """Creates, loads, archives, and deletes Moon Universes.

    The Reflector is constructed with an explicit store path. All
    registry state lives in that store as ordinary files:

        <store>/registry.json
        <store>/snapshots/snap_<id>.json
        <store>/moons/moon_<id>.json
        <store>/archives/moon_<id>.archive.json
    """

    def __init__(self, store: str | Path) -> None:
        self.store = Path(store)
        (self.store / "snapshots").mkdir(parents=True, exist_ok=True)
        (self.store / "moons").mkdir(parents=True, exist_ok=True)
        (self.store / "archives").mkdir(parents=True, exist_ok=True)
        self._registry_path = self.store / "registry.json"
        if self._registry_path.exists():
            self._registry: dict = json.loads(
                self._registry_path.read_text(encoding="utf-8"))
        else:
            self._registry = {"moons": {}}
            self._save_registry()

    # -- registry -------------------------------------------------

    def _save_registry(self) -> None:
        self._registry_path.write_text(
            json.dumps(self._registry, indent=2) + "\n",
            encoding="utf-8")

    def registry(self) -> dict:
        """A copy of the Moon Registry (visible and serializable)."""
        return json.loads(json.dumps(self._registry))

    def _record(self, moon_id: str) -> dict:
        try:
            return self._registry["moons"][moon_id]
        except KeyError:
            raise MoonlightError(
                f"unknown moon_id (not in registry): {moon_id}"
            ) from None

    def list_moons(self) -> list[dict]:
        """All registry records, including archived and deleted
        Moons -- the registry is itself part of the biography."""
        return [dict(r) for r in self._registry["moons"].values()]

    # -- reflection (ML-P1 Sections 3-7) --------------------------

    def create_moon(
        self,
        parent: Universe,
        moon_type: str,
        purpose: str,
    ) -> Universe:
        """Reflect a snapshot of `parent` into a new Moon Universe.

        Emits `reflection_created` (the continuity claim, with
        snapshot evidence and reflection lineage) and `moon_created`
        into the Moon's history, and `moon_created` into the
        parent's history (ML-P1 Section 10). The parent object is
        otherwise untouched, and the Moon shares no mutable state
        with it.
        """
        if moon_type not in MOON_TYPES:
            raise MoonlightError(
                f"invalid moon_type: {moon_type!r} "
                f"(valid: {', '.join(MOON_TYPES)})")

        # The snapshot: the parent's serialized state, preserved as
        # a store artifact -- constitutional evidence of origin.
        snapshot_id = _mint("snap")
        snapshot_path = (self.store / "snapshots"
                         / _filename(snapshot_id))
        parent.save(snapshot_path)
        snapshot_sha = hashlib.sha256(
            snapshot_path.read_bytes()).hexdigest()

        # The Moon: an independent deserialized object graph.
        moon = Universe.load(snapshot_path)
        moon_id = _mint("moon")
        moon.universe_id = moon_id
        moon.created_at = _now()
        moon.snapshot_at = _now()
        moon.meta["moon"] = {
            "moon_id": moon_id,
            "moon_type": moon_type,
            "parent_universe": parent.universe_id,
            "snapshot_id": snapshot_id,
            "created_at": moon.created_at.isoformat(),
            "purpose": purpose,
        }

        lineage = {"origin_universe": parent.universe_id,
                   "snapshot_id": snapshot_id}
        moon._emit_history("reflection_created", moon_id, {
            **_PRODUCER,
            "moon_id": moon_id,
            "moon_type": moon_type,
            "purpose": purpose,
            "origin_universe": parent.universe_id,
            "snapshot_id": snapshot_id,
            "snapshot_sha256": snapshot_sha,
            "entity_count": len(moon.nodes),
            "lineage": lineage,
        })
        moon._emit_history("moon_created", moon_id, {
            **_PRODUCER, "moon_id": moon_id, "moon_type": moon_type,
        })

        moon_path = self.store / "moons" / _filename(moon_id)
        moon.save(moon_path)
        self._registry["moons"][moon_id] = {
            "moon_id": moon_id,
            "moon_type": moon_type,
            "storage_path": moon_path.relative_to(
                self.store).as_posix(),
            "status": "active",
            "parent_universe": parent.universe_id,
            "snapshot_id": snapshot_id,
            "created_at": moon.created_at.isoformat(),
            "state_hash": _state_hash(moon),
        }
        self._save_registry()

        # The Sun records that the Moon existed (ML-P1 Section 10).
        parent._emit_history("moon_created", moon_id, {
            **_PRODUCER,
            "moon_id": moon_id,
            "moon_type": moon_type,
            "snapshot_id": snapshot_id,
        })
        return moon

    # -- loading and saving ---------------------------------------

    def load_moon(self, moon_id: str) -> Universe:
        """Load an active Moon, resolving exclusively through the
        registry. The load itself is recorded (moon_loaded) in the
        Moon's biography and persisted."""
        record = self._record(moon_id)
        if record["status"] != "active":
            raise MoonlightError(
                f"moon {moon_id} is {record['status']}, not active; "
                "archived Moons are read via load_archive()")
        moon = Universe.load(self.store / record["storage_path"])
        moon._emit_history("moon_loaded", moon_id, {**_PRODUCER,
                                                     "moon_id": moon_id})
        moon.save(self.store / record["storage_path"])
        return moon

    def save_moon(self, moon: Universe) -> bool:
        """Persist a Moon back to the store. Emits moon_modified
        when the Moon's state (excluding history) changed since it
        was last stored. Returns True when a modification was
        recorded."""
        record = self._record(moon.universe_id)
        if record["status"] != "active":
            raise MoonlightError(
                f"moon {moon.universe_id} is {record['status']}, "
                "not active; it cannot be saved")
        new_hash = _state_hash(moon)
        modified = new_hash != record["state_hash"]
        if modified:
            moon._emit_history("moon_modified", moon.universe_id, {
                **_PRODUCER, "moon_id": moon.universe_id})
            record["state_hash"] = new_hash
            self._save_registry()
        moon.save(self.store / record["storage_path"])
        return modified

    # -- archival and deletion (ML-P1 Sections 8-9) ---------------

    def archive_moon(
        self, moon_id: str, sun: Universe | None = None
    ) -> dict:
        """Archive a Moon: preserve its complete biography and final
        state as an archive bundle, and mark it archived in the
        registry. If the Sun Universe object is supplied, its
        history records moon_archived (ML-P1 Section 10)."""
        record = self._record(moon_id)
        if record["status"] != "active":
            raise MoonlightError(
                f"moon {moon_id} is {record['status']}, not active; "
                "only an active Moon can be archived")
        moon = Universe.load(self.store / record["storage_path"])
        moon._emit_history("moon_archived", moon_id, {
            **_PRODUCER, "moon_id": moon_id})
        meta = moon.meta.get("moon", {})
        bundle = {
            "moon_id": moon_id,
            "moon_type": record["moon_type"],
            "parent_universe": record["parent_universe"],
            "snapshot_id": record["snapshot_id"],
            "created_at": record["created_at"],
            "purpose": meta.get("purpose", ""),
            "archived_at": _now().isoformat(),
            "history": moon.history,
            "moon": moon.to_dict(),
        }
        archive_path = (self.store / "archives"
                        / _filename(moon_id, ".archive.json"))
        archive_path.write_text(
            json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        record["status"] = "archived"
        record["archive_path"] = archive_path.relative_to(
            self.store).as_posix()
        record["archived_at"] = bundle["archived_at"]
        self._save_registry()
        if sun is not None:
            sun._emit_history("moon_archived", moon_id, {
                **_PRODUCER, "moon_id": moon_id,
                "archive_path": record["archive_path"]})
        return bundle

    def load_archive(self, moon_id: str) -> dict:
        """Read a Moon's archive bundle -- its biography survives
        the Moon, including after deletion."""
        record = self._record(moon_id)
        if "archive_path" not in record:
            raise MoonlightError(
                f"moon {moon_id} has no archive")
        return json.loads(
            (self.store / record["archive_path"]).read_text(
                encoding="utf-8"))

    def delete_moon(self, moon_id: str) -> dict:
        """Delete an active Moon file. REFUSES unless a verified
        archive exists (ML-P1 ruling, Finding 3): the required order
        is archive -> verify archive -> delete. The registry record
        and the archive -- the Moon's biography -- are retained."""
        record = self._record(moon_id)
        if record["status"] == "deleted":
            raise MoonlightError(f"moon {moon_id} is already deleted")
        if record["status"] != "archived":
            raise MoonlightError(
                f"delete refused: no archive exists for {moon_id}; "
                "archive the Moon before deleting it")
        # Verify the archive before anything is removed.
        bundle = self.load_archive(moon_id)
        event_types = [e.get("event_type")
                       for e in bundle.get("history", [])]
        if (bundle.get("moon_id") != moon_id
                or "moon_archived" not in event_types):
            raise MoonlightError(
                f"delete refused: archive for {moon_id} failed "
                "verification")
        moon_path = self.store / record["storage_path"]
        if moon_path.exists():
            moon_path.unlink()
        record["status"] = "deleted"
        record["deleted_at"] = _now().isoformat()
        self._save_registry()
        return dict(record)
