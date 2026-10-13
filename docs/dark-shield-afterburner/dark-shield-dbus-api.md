# Dark Shield D-Bus API Design

*Design note by Jordan, October 9, 2026.*

Given the Dark Shield concepts of Moonlight, Data Gravity, Antigravity, Afterburner, Reality Anchors, Pulsars, Temporal Echoes, and Galaxies, a clean D-Bus design should expose only control-plane orchestration interfaces while high-volume workloads remain on gRPC and Unix sockets. The vision positions these services as coordinating experimentation, relationships, future-state analysis, and protected promotion into the trusted Sun Universe.

## D-Bus Naming Convention

### Bus Names

```
org.darkshield.Universe
org.darkshield.Gravity
org.darkshield.DarkMatter
org.darkshield.Antigravity
org.darkshield.Eclipse
org.darkshield.Moonlight
org.darkshield.Afterburner
org.darkshield.Consensus
org.darkshield.Observatory
org.darkshield.Anchor
```

### Object Paths

```
/org/darkshield/universe
/org/darkshield/gravity
/org/darkshield/darkmatter
/org/darkshield/antigravity
/org/darkshield/eclipse
/org/darkshield/moonlight
/org/darkshield/afterburner
/org/darkshield/consensus
/org/darkshield/observatory
/org/darkshield/anchor
```

## Universe Interface

```xml
<interface name="org.darkshield.Universe">
```

The Universe service manages the continuously evolving system state envisioned by Persistent Boot.

Methods:

```
GetUniverseState() → (s state)

ListGalaxies() → (as galaxies)

GetGalaxy(s galaxy_id) → (a{sv} galaxy)

GetUniverseMetrics() → (a{sv} metrics)

ReloadUniverse() → ()
```

Signals:

```
UniverseChanged(s universe_id)

GalaxyCreated(s galaxy_id)

GalaxyRemoved(s galaxy_id)
```

## Gravity Interface

The Gravity interface models relationship networks between Stars, Pulsars, Galaxies, and user activity.

```xml
<interface name="org.darkshield.Gravity">
```

Methods:

```
GetGravityScore(s node) → (d score)

GetRelationships(s node) → (aa{sv} relationships)

CalculateGravityField(as nodes) → (a{sv} gravity_field)

FindClusters(s galaxy) → (as cluster_ids)
```

Signals:

```
GravityShiftDetected(s node, d delta)
```

## Dark Matter Interface

The Dark Matter service reveals hidden metadata, dependency paths, permissions, and historical connections.

```xml
<interface name="org.darkshield.DarkMatter">
```

Methods:

```
RevealDependencies(s object) → (as dependencies)

RevealHistory(s object) → (aa{sv} history)

RevealPermissionGraph(s object) → (aa{sv} permissions)

GetDarkMatterScore(s object) → (d score)
```

Signals:

```
HiddenRelationshipDiscovered(s source, s target)
```

## Eclipse Interface

The Eclipse service identifies windows of elevated evolutionary potential.

```xml
<interface name="org.darkshield.Eclipse">
```

Methods:

```
DetectEclipse() → (a{sv} eclipse)

GetActiveEclipses() → (aa{sv} eclipses)

GetTwinkles() → (aa{sv} twinkles)

GetEvolutionPotential(s galaxy) → (d score)
```

Signals:

```
EclipseDetected(s eclipse_id, d strength)

EclipseEnded(s eclipse_id)
```

## Antigravity Interface

Antigravity predicts future possibilities and alternative states.

```xml
<interface name="org.darkshield.Antigravity">
```

Methods:

```
PredictFuture(a{sv} context) → (a{sv} future)

ListCandidateFutures(s target) → (aa{sv} futures)

RankFuture(s future_id) → (d rank)
```

Signals:

```
FutureDiscovered(s future_id)
```

## Moonlight Interface

Moonlight creates and manages experimental universes.

```xml
<interface name="org.darkshield.Moonlight">
```

Methods:

```
CreateUniverse(s template, s strategy) → (s universe_id)

PauseUniverse(s universe_id) → ()

ResumeUniverse(s universe_id) → ()

DestroyUniverse(s universe_id) → ()

GetUniverseStatus(s universe_id) → (a{sv} status)

ListUniverses() → (as universe_ids)

PromoteUniverse(s universe_id) → (b accepted)
```

Signals:

```
UniverseCreated(s universe_id)

UniverseFailed(s universe_id)

UniverseReadyForPromotion(s universe_id)
```

## Afterburner Interface

Afterburner accelerates experimentation during Eclipse Events.

```xml
<interface name="org.darkshield.Afterburner">
```

Methods:

```
Ignite(s universe_id, s intensity) → (b success)

Throttle(s universe_id, d factor) → ()

Shutdown(s universe_id) → ()

GetAfterburnerMetrics(s universe_id) → (a{sv} metrics)
```

Signals:

```
AfterburnerStarted(s universe_id)

AfterburnerCompleted(s universe_id)

AfterburnerOverload(s universe_id)
```

## Consensus Interface

Evaluates competing Moon Universes and selects winning outcomes.

```xml
<interface name="org.darkshield.Consensus">
```

Methods:

```
EvaluateUniverses(as universe_ids) → (a{sv} decision)

CompareUniverses(s universe_a, s universe_b) → (a{sv} result)

GetWinner(as candidates) → (s winner)
```

Signals:

```
ConsensusReached(s universe_id, d confidence)
```

## Observatory Interface

Observes Pulsars, resource activity, evolution metrics, and universe health.

```xml
<interface name="org.darkshield.Observatory">
```

Methods:

```
GetMetrics() → (a{sv} metrics)

GetUniverseMetrics(s universe_id) → (a{sv} metrics)

GetPulsars() → (aa{sv} pulsars)

GetTemporalEchoes(s universe_id) → (aa{sv} echoes)
```

Signals:

```
AnomalyDetected(s universe_id, s category)

MetricThresholdExceeded(s metric, d value)
```

## Reality Anchor Interface

Reality Anchors protect trusted structures and must approve evolution returning to the Sun Universe.

```xml
<interface name="org.darkshield.Anchor">
```

Methods:

```
VerifyState(s universe_id) → (b trusted)

LockAnchor(s anchor_id) → ()

UnlockAnchor(s anchor_id) → ()

ApprovePromotion(s universe_id) → (b approved)

GetAnchorStatus() → (a{sv} status)
```

Signals:

```
AnchorViolationDetected(s anchor_id)

PromotionApproved(s universe_id)

PromotionRejected(s universe_id)
```

## Standard Object Model

Every interface should share a common identity schema:

```
star://<id>
pulsar://<id>
galaxy://<id>
moon://<id>
future://<id>
echo://<id>
anchor://<id>
```

This gives Dark Shield a coherent D-Bus API surface where Moonlight orchestrates universes, Antigravity predicts futures, Gravity models relationships, Afterburner accelerates evolution, Observatory measures outcomes, and Reality Anchors govern trust before any experiment can affect the Sun Universe.

---

## v2 Changelog (October 9, 2026)

A revised production contract lives in `../dark-shield-dbus/v2/` (12 files + README), incorporating independent review feedback:

1. Standard freedesktop interfaces (`Introspectable`, `Properties`, `Peer`) on every object.
2. Error contract `org.darkshield.Error.*`: `NotFound`, `InvalidUniverse`, `AnchorViolation`, `ResourceExhausted`, `PermissionDenied`, `EclipseRequired`.
3. Three-way promotion handshake: `Moonlight.RequestPromotion` → `Consensus.EvaluatePromotion` → `Anchor.ApprovePromotion` (single ownership per operation; the Anchor is sole approver).
4. Dynamic object hierarchy: `org.darkshield.MoonUniverse` at `/org/darkshield/moons/<moon_id>`, `org.darkshield.Galaxy` at `/org/darkshield/galaxies/<galaxy_id>`.
5. Stable struct types where shapes are fixed: `GetGravityEdges` → `a(ssd)`, `GetPulsarLoad` → `a(sddd)`; loose `a{sv}` kept where shapes still evolve.

All v2 files validated as well-formed XML.
