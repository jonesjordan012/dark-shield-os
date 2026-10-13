# Dark Shield IPC Layer — the Nervous System of the Universe

*Design note by Jordan, October 9, 2026.*

For Dark Shield, the IPC layer is the nervous system of the universe. The vision already establishes Stars, Pulsars, Galaxies, Data Gravity, Moonlight, Afterburner, Antigravity, and Reality Anchors as cooperating subsystems. The goal is to make every subsystem independently replaceable while preserving a consistent API.

## IPC Technology Selection

| Layer               | Linux Technology          |
|---------------------|---------------------------|
| Service Control     | systemd + D-Bus           |
| Event Distribution  | D-Bus Signals             |
| High Volume Telemetry | Unix Domain Sockets     |
| Graph Queries       | gRPC over Unix Socket     |
| Moon Universe Control | REST/gRPC               |
| Observability       | OpenTelemetry             |
| Shared Data         | SQLite/Postgres           |
| Kernel Events       | eBPF Ring Buffers         |

## Control Plane IPC

### Universe Bus

The central message bus.

```
unix:///run/darkshield/universe.sock
```

Implemented through D-Bus. Service name: `org.darkshield.Universe`.

Every major service registers here:

```
org.darkshield.Gravity
org.darkshield.Moonlight
org.darkshield.Afterburner
org.darkshield.Antigravity
org.darkshield.Observatory
org.darkshield.Eclipse
```

### Eclipse Detection Contract

Service: `org.darkshield.Eclipse`

Method: `detect()`

Response:

```json
{
  "eclipse_id": "ECL-00124",
  "severity": "HIGH",
  "twinkles": 284,
  "candidate_futures": 94
}
```

Signal: `EclipseDetected`

Payload:

```json
{
  "severity": "HIGH",
  "galaxy": "Development"
}
```

### Antigravity API

The vision defines Antigravity as a prediction engine for alternative futures.

Service: `org.darkshield.Antigravity`

Method: `predict_future()`

Request:

```json
{
  "target": "galaxy://development",
  "scope": "optimization"
}
```

Response:

```json
{
  "future_id": "F-782",
  "probability": 0.84,
  "value": 0.92,
  "risk": 0.11
}
```

### Data Gravity API

The vision defines Data Gravity as relationships between information, processes, services, and activity.

Service: `org.darkshield.Gravity`

Methods: `get_relationships()`, `calculate_gravity()`

Request:

```json
{
  "node": "star://kernel.py"
}
```

Response:

```json
{
  "gravity_score": 91,
  "connected_nodes": 412
}
```

### Dark Matter API

The vision defines Dark Matter as hidden metadata, dependencies, and histories.

Method: `reveal()`

Request:

```json
{
  "object": "star://database.py"
}
```

Response:

```json
{
  "dependencies": 68,
  "permission_paths": 12,
  "historical_links": 42
}
```

### Moonlight Control API

The vision describes Moonlight as the mechanism that creates experimental universes.

Service: `org.darkshield.Moonlight`

Methods: `create_universe()`, `destroy_universe()`, `pause_universe()`, `promote_universe()`

Create universe request:

```json
{
  "template": "sun-current",
  "goal": "performance"
}
```

Response:

```json
{
  "universe_id": "moon-0091",
  "state": "RUNNING"
}
```

Universe status request:

```json
{
  "universe_id": "moon-0091"
}
```

Response:

```json
{
  "state": "RUNNING",
  "strategy": "performance"
}
```

### Afterburner API

The vision defines Afterburner as accelerated experimentation available during Eclipse Events.

Service: `org.darkshield.Afterburner`

Methods: `ignite()`, `throttle()`, `shutdown()`

Request:

```json
{
  "universe": "moon-0091",
  "intensity": "MAXIMUM"
}
```

Response:

```json
{
  "workers": 2048,
  "experiments_per_second": 5500
}
```

### Consensus API

Determines winning futures.

Service: `org.darkshield.Consensus`

Method: `evaluate()`

Input:

```json
{
  "universes": ["moon-001", "moon-002", "moon-003"]
}
```

Output:

```json
{
  "winner": "moon-002",
  "confidence": 0.89
}
```

## Data Plane IPC

The Data Plane handles high-volume execution traffic. D-Bus is too slow. Use Unix Domain Sockets, gRPC, Shared Memory.

### Universe Factory Contract

Service: `darkshield-universe-factory`

Socket: `/run/darkshield/factory.sock`

Create universe:

```json
{
  "snapshot": "sun-842",
  "profile": "creative"
}
```

Response:

```json
{
  "universe": "moon-1001"
}
```

### Reflection Layer Contract

The vision describes Moonlight reflections as experimental copies of reality.

Request:

```json
{
  "source": "sun",
  "target": "moon-1001"
}
```

Response:

```json
{
  "snapshot": "btrfs-8842",
  "size": "24MB"
}
```

### Pulsar Contract

Pulsars represent active computation.

Socket: `/run/darkshield/pulsar.sock`

Telemetry (published every second):

```json
{
  "cpu": 82.4,
  "memory": 43.2,
  "io": 12.3
}
```

### Temporal Echo Contract

The vision defines Temporal Echoes as visible artifacts of activity over time. Append-only event stream.

Event:

```json
{
  "event_type": "UNIVERSE_EVOLUTION",
  "source": "moon-0091",
  "timestamp": "...",
  "changes": 34
}
```

### Reality Anchor Contract

Reality Anchors preserve system integrity. This API is intentionally restrictive.

Service: `org.darkshield.Anchor`

Methods: `verify()`, `lock()`, `approve_promotion()`

Example:

```json
{
  "promotion": "moon-0091"
}
```

Response:

```json
{
  "approved": true,
  "signature": "anchor-8fa9..."
}
```

## Canonical Service Map

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

## Architectural Rule

Architecturally, the cleanest rule is:

- **D-Bus for decisions.**
- **gRPC for services.**
- **Unix sockets for telemetry.**
- **Event streams for Temporal Echoes.**

Reality Anchors approve every change crossing from a Moon Universe back into the Sun Universe.
