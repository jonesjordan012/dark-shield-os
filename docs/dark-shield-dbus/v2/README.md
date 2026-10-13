# Dark Shield D-Bus API — v2

Production-grade D-Bus introspection contract for the Moonlight Control Plane, revised per independent review.

## v2 changes

1. **Standard freedesktop interfaces** — every object now declares
   `org.freedesktop.DBus.Introspectable`, `org.freedesktop.DBus.Properties`,
   and `org.freedesktop.DBus.Peer` for tooling compatibility.
2. **Error contract** — `org.darkshield.Error.*` names documented per method:
   `NotFound`, `InvalidUniverse`, `AnchorViolation`, `ResourceExhausted`,
   `PermissionDenied`, `EclipseRequired`. (Note `EclipseRequired`: some
   operations, e.g. `Afterburner.Ignite`, can only run during an eclipse.)
3. **Three-way promotion handshake** (single ownership per operation):
   `Moonlight.RequestPromotion` → `Consensus.EvaluatePromotion` →
   `Anchor.ApprovePromotion`. The Anchor is the sole approver; nothing
   crosses from a Moon Universe into the Sun Universe without it.
4. **Dynamic object hierarchy** — new per-object interfaces:
   - `org.darkshield.MoonUniverse` at `/org/darkshield/moons/<moon_id>`
   - `org.darkshield.Galaxy` at `/org/darkshield/galaxies/<galaxy_id>`
5. **Stable struct types** where shapes are fixed:
   - `Gravity.GetGravityEdges` → `a(ssd)` (source, target, weight)
   - `Observatory.GetPulsarLoad` → `a(sddd)` (pulsar_id, cpu, memory, io)
   
   Loose `a{sv}` dictionaries are kept where the shape is still evolving
   (futures, universe status, metrics).

## Object tree

```
/org/darkshield
├── universe
├── gravity
├── darkmatter
├── eclipse
├── antigravity
├── afterburner
├── consensus
├── observatory
├── anchor
├── galaxies
│   ├── development
│   ├── learning
│   └── creativity
└── moons
    ├── moon0091
    ├── moon0092
    └── moon0093
```

## Promotion handshake flow

```
Moonlight.RequestPromotion(moon-0091) → request_id "PR-552"
        │  signal: PromotionRequested
        ▼
Consensus.EvaluatePromotion("PR-552") → {confidence: 0.89, ...}
        │  signal: PromotionEvaluated
        ▼
Anchor.ApprovePromotion("PR-552") → true
        │  signal: PromotionApproved
        ▼
Sun Universe inherits the evolution
```

## Files

| File | Interface |
|---|---|
| org.darkshield.Universe.xml | org.darkshield.Universe |
| org.darkshield.Gravity.xml | org.darkshield.Gravity |
| org.darkshield.DarkMatter.xml | org.darkshield.DarkMatter |
| org.darkshield.Eclipse.xml | org.darkshield.Eclipse |
| org.darkshield.Antigravity.xml | org.darkshield.Antigravity |
| org.darkshield.Moonlight.xml | org.darkshield.Moonlight |
| org.darkshield.Afterburner.xml | org.darkshield.Afterburner |
| org.darkshield.Consensus.xml | org.darkshield.Consensus |
| org.darkshield.Observatory.xml | org.darkshield.Observatory |
| org.darkshield.Anchor.xml | org.darkshield.Anchor |
| org.darkshield.MoonUniverse.xml | org.darkshield.MoonUniverse (per-moon) |
| org.darkshield.Galaxy.xml | org.darkshield.Galaxy (per-galaxy) |

Suitable for implementation with sd-bus, GDBus, dbus-broker, or Rust's zbus.
Data-plane workloads remain on gRPC and Unix sockets.

## Planned v3 scope (parked)

Per review, v3 should focus exclusively on production hardening rather than
new conceptual services:

1. **API versioning** — versioned interface names or version properties so
   implementations can evolve without breaking clients.
2. **ObjectManager support** — `org.freedesktop.DBus.ObjectManager` with
   `GetManagedObjects` / `InterfacesAdded` / `InterfacesRemoved` for the
   dynamic `/org/darkshield/moons/*` and `/org/darkshield/galaxies/*` trees.
3. **Enum definitions** — canonical string enums for severity levels,
   intensities, strategies, and states currently passed as free strings.
4. **Security policy integration** — D-Bus busconfig allow/deny policy per
   service, SELinux/AppArmor confinement, tied to the Reality Anchor trust
   story (TPM, Secure Boot, dm-verity per the Linux mapping).

v3 is intentionally deferred until a prototype implementation exists, since
building will revise the spec.
