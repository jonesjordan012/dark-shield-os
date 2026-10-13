# Moonlight Multiverse Architecture — one spec

*Consolidated October 10, 2026, from Jordan's design notes of October 9, 2026: the Convergence Eclipse note, the Moonlight Parallel Universe Architecture (9 layers), and the Moonlight Control Plane / Data Plane design. Nothing here is new invention — every idea below is his. This document puts the three notes in one frame, shows where the two architectural views agree and overlap, and names the questions still open. Weights, thresholds, and open questions are his to decide.*

Related documents: the Afterburner force function spec (`dark-shield-afterburner-force-function.md`) makes the Convergence Eclipse *computable*; the D-Bus v2 API (`../dark-shield-dbus/v2/`) defines the promotion handshake contracts; the merge-mechanics brief (`dark-shield-moonlight-merge-mechanics.md`, drafted October 11 from the October 9–10 research) attacks the deepest open challenge.

## Moonlight in one paragraph

Dark Shield's trusted world is the **Sun Universe** — your data, your identity, the system you rely on. Nothing experimental ever touches it directly. Instead, when the system senses a good moment (an **Eclipse**), **Moonlight** takes a *reflection* of the Sun — a copy-on-write snapshot where shared things stay shared and only changed things cost extra — and spins up many independent **Moon Universes**, each given a mission (faster, safer, simpler, more creative, deliberately chaotic). Each moon runs its own experiments at full speed. An observatory watches everything; a consensus engine compares all the outcomes; the best traits are merged back into the Sun through a guarded promotion handshake. The failed moons are simply discarded. Every Moon Universe is disposable. The Sun — and the Reality Anchors that protect it — are not.

## The core mechanism: reflection, not cloning

This is the engineering insight that makes Moonlight possible, and it came from Jordan's design: Moonlight never clones the whole system. It reflects it.

```
Sun Universe (snapshot)
│
┌──────────┼──────────┐
│          │          │
Moon A   Moon B   Moon C   ... Moon N
perf     security creativity
```

Shared objects remain linked to the Sun. Only modified structures consume additional resources — this is the same copy-on-write principle behind Btrfs/ZFS snapshots and OverlayFS (see the Linux mapping doc), which means hundreds or thousands of moons are affordable, not science fiction. A moon is a question the universe asks itself: *"what if we changed this?"*

## The system as two planes

Jordan produced two architectural views of the same system: a 9-layer design and a control-plane / data-plane split. They are not two systems — the control/data split is the cleaner organizing frame, and the 9 layers map onto it as follows.

**The rule:** the Control Plane *imagines* futures. The Data Plane *explores* futures. Neither crosses the Reality Anchor Boundary.

```
┌────────────────── CONTROL PLANE (imagines) ──────────────────┐
│ Eclipse Detection · Antigravity Engine · Gravity Map         │
│ Dark Matter Decoder · Universe Scheduler · Consensus Engine  │
│                ▲ telemetry feedback ▲                        │
└────────────────┼─────────────────────────────────────────────┘
                 │   REALITY ANCHOR BOUNDARY
                 │   (identity, permissions, ownership, security
                 │    policies, critical data — nothing bypasses it)
┌────────────────┼─────────────────────────────────────────────┐
│ Universe Factory · Reflection Layer · Afterburner Engines    │
│ Pulsar Execution Grid · Temporal Echo Recorder · Observatory │
└────────────────── DATA PLANE (explores) ─────────────────────┘
```

Where the 9 layers land:

| 9-layer view | Lives in | What it does there |
|---|---|---|
| Layer 1 — Sun Universe | Outside / above | The trusted source of truth; reflected, never experimented on |
| Layer 2 — Reflection Engine | Data plane | Copy-on-write reflection of Sun into moons |
| Layer 3 — Universe Specialization | Data plane (+ scheduler) | Each moon gets a mission: performance, security, creativity, learning, chaos |
| Layer 4 — Antigravity Prediction Core | Control plane | Ranks futures; not every future deserves a moon |
| Layer 5 — Distributed Afterburner | Data plane | One Afterburner per moon, each on a different axis |
| Layer 6 — Reality Anchor Network | The boundary | Anchors sit *outside* all moons; even a catastrophic moon failure can't touch them |
| Layer 7 — Universe Observatory | Data plane → control | Telemetry (gravity, pulsar, galaxy, temporal-echo metrics) feeds back up |
| Layer 8 — Consensus Engine | Control plane | Compares all evolved futures; decides what gets promoted |
| Layer 9 — Galaxy-Level Evolution | Control plane (scheduler) | Moons specialize by galaxy — each human intention evolves independently |

The two views agree on everything substantive. The control/data split adds one thing the 9-layer view implied but didn't state: **the Universe Scheduler closes the compute-budget gap** — force is advice, the budget is law.

## The lifecycle of one experiment, end to end

1. **Eclipse detected.** The Eclipse Detection Engine watches twinkling stars, bottlenecks, security anomalies, relationship changes, and user activity shifts. An eclipse is a temporary window of elevated evolutionary potential — many galaxies changing at once, projects hitting milestones, new information flooding in, old structures reaching their limits.

2. **Antigravity ranks the futures.** The prediction engine proposes possible futures and ranks them by expected gain and risk. *"Data gravity reveals what exists. Dark matter reveals why it exists. Antigravity reveals what could exist."* Only futures worth exploring get moons.

3. **The Scheduler spins moons.** Each moon gets a mission. The classic set: performance, security, creativity, learning — plus the **Chaos Universe**, which deliberately tries to break assumptions and discover edge cases.

4. **Afterburners run.** Each moon runs its own Afterburner strategy in parallel — refactoring, process optimization, relationship restructuring, large-scale simulation — accelerated by the Pulsar Execution Grid, recorded by the Temporal Echo Recorder.

5. **The Observatory watches.** Gravity, pulsar, galaxy, and temporal-echo metrics stream back to the control plane.

6. **Consensus compares everything.** Not one winner — the best *traits* from multiple moons can be merged:
   - Which future performs best? Safest? Improves human agency? Reveals useful knowledge?

7. **Promotion — the guarded handshake.** Merging back into the Sun goes through the three-way handshake defined in the D-Bus v2 contract: **Request → Evaluate → Approve**, with the **Reality Anchor as sole approver**. This is the system's immune system.

8. **The Sun inherits; the moons die.** Only the most successful evolutionary traits return. Failed moons are discarded, cost-free.

## The peak state: Convergence Eclipse

Jordan's theoretical maximum — the moment all evolutionary signals align at once:

- Massive twinkling (thousands of optimization opportunities visible)
- Strong data gravity (dense, rich relationship networks)
- Maximum dark matter visibility (hidden structures fully mapped)
- A major eclipse (the perfect window)
- Many moons, one per optimization axis (performance, security, simplicity, creativity, energy, novel structures…)
- Antigravity at full amplification (most promising futures, highest gains, lowest risks)
- Reality Anchors rock-solid (the stronger the anchors, the more aggressively the moons may explore)

This is now computable: the Afterburner force function spec turns the Convergence Eclipse into a number F between 0 and 1, recomputed every tick, with **Convergence Eclipse** as the regime where F ≥ 0.8 *and* anchor trust R ≥ 0.95. The triad is the whole philosophy in one line: *gravity reveals what exists, dark matter reveals why, antigravity reveals what could exist.*

## Open questions (Jordan's to decide)

1. **Merge mechanics** — the deep open challenge. Consensus can pick the best traits, but *how do traits from different moons combine without breaking the Sun?* The merge-mechanics brief (`dark-shield-moonlight-merge-mechanics.md`, drafted October 11 from the October 9–10 research) is the attack on this problem; it is not solved here.
2. **Chaos Universe trust boundary.** Should the deliberately-destructive chaos moon run inside the same anchor boundary as the others, or in a harder sandbox of its own? Recommended: harder sandbox — but it's his call.
3. **Promotion handshake detail.** The D-Bus v2 contract defines Request → Evaluate → Approve at the API level; the PromoteUniverse → ApprovePromotion flow between the Moonlight and Anchor interfaces still needs its explicit step-by-step definition (noted in the IPC layer doc).
4. **Scheduler policy.** When force says "go" and the compute budget says "no," the budget wins (already settled in the force-function spec) — but the default budget sizing per tick is still undefined.
5. **Bus policy (parked with v3).** SELinux/AppArmor policy for the D-Bus interfaces remains the one open v3 item; it gates nothing at prototype stage.
