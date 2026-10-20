"""Base entity for the Dark Shield canonical universe graph (M1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import ClassVar


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return _now()
    return datetime.fromisoformat(value)


@dataclass(slots=True)
class Entity:
    """Every Dark Shield entity: stable id, timestamps, reality marking.

    canonical=True  -> this entity is canonical reality.
    derived=True    -> this entity is a derived view/cache (cf. Entry 002).
    The two are mutually exclusive; see UC-14.
    """

    id: str
    name: str
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    canonical: bool = True
    derived: bool = False
    classification_source: str = "filesystem"
    classification_kind: str = ""

    # Schema node type string, e.g. "star". Set by subclasses.
    CLASS_TYPE: ClassVar[str] = "entity"

    # Registry of node type -> entity class, populated by subclasses.
    _registry: ClassVar[dict[str, type[Entity]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        # NOTE: explicit super(Entity, cls), not zero-arg super().
        # @dataclass(slots=True) recreates the class object, which
        # orphans the __class__ cell that zero-arg super() relies on.
        super(Entity, cls).__init_subclass__(**kwargs)
        if cls.CLASS_TYPE != "entity":
            Entity._registry[cls.CLASS_TYPE] = cls

    def __post_init__(self) -> None:
        if self.canonical and self.derived:
            raise ValueError(
                f"{self.id}: canonical and derived are mutually exclusive"
            )

    def properties_dict(self) -> dict:
        """Subclass-specific schema properties. Overridden below."""
        return {}

    def to_dict(self) -> dict:
        """Serialize to a plain JSON-safe dict of the dataclass's fields.

        Round-trips with from_dict(): Star(**star.to_dict()) == star,
        and json.dumps(star.to_dict()) works.
        (For the universe.json schema shape, use to_node_dict().)
        """
        d = asdict(self)
        for key in ("created_at", "updated_at"):
            value = d.get(key)
            if isinstance(value, datetime):
                d[key] = value.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Entity:
        """Reconstruct an entity of this class from to_dict() output."""
        data = dict(data)
        for key in ("created_at", "updated_at"):
            value = data.get(key)
            if isinstance(value, str):
                data[key] = datetime.fromisoformat(value)
        return cls(**data)

    def to_node_dict(self) -> dict:
        """Serialize directly to a universe.json schema node."""
        return {
            "id": self.id,
            "type": self.CLASS_TYPE,
            "name": self.name,
            "canonical": self.canonical,
            "derived": self.derived,
            "classification": {
                "source": self.classification_source,
                "kind": self.classification_kind,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "properties": self.properties_dict(),
        }

    @classmethod
    def from_node_dict(cls, data: dict) -> Entity:
        """Reconstruct an entity from a universe.json schema node.

        Dispatches on the node "type" to the right subclass.
        Round-trips with to_node_dict().
        """
        klass = cls._registry.get(data["type"])
        if klass is None:
            raise ValueError(
                f"unknown node type: {data['type']!r} "
                f"(known: {sorted(cls._registry)})"
            )
        classification = data.get("classification", {})
        return klass(
            id=data["id"],
            name=data["name"],
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
            canonical=data.get("canonical", True),
            derived=data.get("derived", False),
            classification_source=classification.get("source", "filesystem"),
            classification_kind=classification.get("kind", ""),
            **data.get("properties", {}),
        )
