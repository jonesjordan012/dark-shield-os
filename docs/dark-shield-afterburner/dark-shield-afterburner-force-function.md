# Afterburner Force Function — computable spec

*Draft v0.1, October 10, 2026. Built from Jordan's Convergence Eclipse design note (2026-10-09). Awaiting his review — weights and thresholds are his to tune.*

## The idea in one sentence

**Afterburner force is a single number between 0 and 1, recomputed on every tick, that tells Dark Shield how hard to push experimentation right now.** 0 means "sit still." 1 means "maximum exploration, but only if the anchors hold."

This takes the Convergence Eclipse — Jordan's theoretical peak state, where *all* evolutionary signals align at once — and turns it into something a computer can actually calculate, every minute, forever.

## The seven signals

Six signals push force *up*. One — the anchor check — can drag it to *zero* no matter what the others say. That last one is the safety logic Jordan already built into the design: *"Every Moon Universe is disposable. Reality Anchors are not."*

| # | Signal | What it measures, in plain words | Where it comes from (existing contracts) |
|---|--------|----------------------------------|------------------------------------------|
| 1 | **Twinkle density (T)** | How many stars are flashing — flashing means an optimization opportunity was spotted | `Eclipse.GetTwinkles()` returns the twinkle list; the IPC layer already counts them (the example shows 284 in one tick) |
| 2 | **Gravity coherence (G)** | How interconnected the universe is — changes pay off more when relationships are dense enough to carry them | Gravity service metrics (NetworkX graph clustering of the star-relationship graph; a value already between 0 and 1) |
| 3 | **Dark matter visibility (D)** | How much of the hidden structure the system can actually see — you don't experiment blind | Dark matter decoder's coverage fraction: metadata chains + dependency graphs + permission structures fully mapped, divided by all known relationships |
| 4 | **Eclipse state (E)** | Whether we're inside an elevated-potential window right now | `EclipseDetected` D-Bus signal: 0 = no eclipse, 0.5 = minor, 1.0 = major; fades over time after the event |
| 5 | **Antigravity futures (A)** | How many promising predicted futures exist, discounted by their risk | Antigravity engine output: futures with positive expected gain, risk-weighted and log-scaled so 10,000 futures don't crush 100 |
| 6 | **Moonlight capacity (M)** | How many experimental universes we have room to spin up | Universe scheduler: free Moon Universe slots ÷ target slots, capped at 1 |
| 7 | **Anchor trust (R)** | Are the Reality Anchors healthy? — the gatekeeper | Anchor health checks (TPM, SELinux, dm-verity, audit): fraction passing, a value between 0 and 1 |

## Putting everything on the same ruler (normalization)

The signals arrive in different units — twinkle counts, graph fractions, future lists — so each one is first rescaled to a number between 0 and 1. Plain-English rules:

- **Twinkle density:** `T = log(1 + twinkles) / log(1 + 5000)`. The logarithm matters: the difference between 10 and 100 twinkles is a big deal; the difference between 4,000 and 4,100 is noise. 5,000 twinkles per tick is the ceiling that counts as "maximum."
- **Gravity coherence:** already 0–1 (a graph clustering coefficient). No rescaling needed.
- **Dark matter visibility:** already 0–1 (a fraction of mapped relationships).
- **Eclipse state:** 0, 0.5, or 1.0 from the detector, multiplied by a fade factor — `E = state × 0.9^ticks_since_event` — so an eclipse that happened an hour ago matters less than one happening now.
- **Antigravity futures:** `A = risk_discount × log(1 + promising_futures) / log(1 + 500)`. Futures with expected gain below a cutoff don't count; the rest are scaled against a ceiling of 500.
- **Moonlight capacity:** `M = min(1, free_slots / target_slots)`.
- **Anchor trust:** already 0–1. No rescaling.

## The function

```
F = R × (0.20·T + 0.15·G + 0.15·D + 0.20·E + 0.15·A + 0.15·M)
```

Two design choices, stated plainly so Jordan can argue with them:

1. **Additive for opportunity, multiplicative for safety.** The six opportunity signals are *weighted and added* — any one strong signal can raise the force on its own. But the whole sum is *multiplied* by anchor trust, so if the anchors fail (R → 0), force collapses to zero no matter how tempting the opportunities look. Safety is never outvoted.
2. **Weights are votes.** Each weight is how much that signal's vote counts; they sum to 1. Eclipse state and twinkle density get the biggest votes (0.20 each) because they are the most direct measures of "now is a good time to experiment." These defaults are a starting point, not a law.

## The four regimes (thresholds)

| Force | Regime | What Dark Shield does |
|-------|--------|----------------------|
| F < 0.2 | **DORMANT** | No Afterburner. Twinkles are logged, nothing is experimented with. |
| 0.2 ≤ F < 0.5 | **EMBER** | A few Moon Universes on low-priority axes (e.g., simplicity, energy efficiency). Cheap, safe exploration. |
| 0.5 ≤ F < 0.8 | **ECLIPSE** | Full Afterburner on the priority axes (performance, security, creativity). This is the normal working state of the evolution engine. |
| F ≥ 0.8 **and** R ≥ 0.95 | **CONVERGENCE ECLIPSE** | Every machine axis (AB-1 through AB-7), maximum universes. AB-8 First Citizen is never force-driven and never contained in the Eclipse: peak force never summons the Citizen — the Citizen summons themselves, as a fresh human act ("All Systems Go"). Per Jordan's ruling 2026-10-12: Convergence Eclipse = machine maximum confidence; AB-8 = citizen maximum responsibility. This is Jordan's theoretical peak — reachable only when *all* signals are high *and* the anchors are near-perfect. |

**Hysteresis (anti-flicker rule):** a regime engages when F crosses its threshold going up, but disengages only when F falls 0.1 *below* the threshold going down. Without this, the system would stutter on and off at the boundary.

**Budget caps (anti-runaway rule):** the Universe Scheduler keeps a compute budget per tick. Even at Convergence Eclipse, force can never authorize more universes than the budget allows. If force says "go" and the budget says "no," the budget wins — force is advice, the budget is law.

## Worked example — does it breathe?

A busy Saturday in a mature Dark Shield universe:

- 284 twinkles this tick (the number already in the IPC layer example) → `T = log(285)/log(5001) ≈ 0.66`
- Relationship graph clustering 0.60 → `G = 0.60`
- 45% of relationships fully mapped → `D = 0.45`
- Major eclipse detected this tick → `E = 1.0`
- 120 promising futures, risk discount 0.8 → `A ≈ 0.74`
- 6 of 12 Moon slots free → `M = 0.50`
- All anchor checks passing, one warning → `R = 0.98`

```
F = 0.98 × (0.20×0.66 + 0.15×0.60 + 0.15×0.45 + 0.20×1.00 + 0.15×0.74 + 0.15×0.50)
  = 0.98 × (0.132 + 0.090 + 0.0675 + 0.200 + 0.111 + 0.075)
  = 0.98 × 0.6755
  ≈ 0.66  →  ECLIPSE regime
```

The universe is busy and experimenting hard — but not at Convergence, because dark matter visibility (0.45) and spare capacity (0.50) are middling. That matches the design intent: Convergence Eclipse should be *rare*, the peak Jordan described, not an everyday occurrence.

## How it plugs into the existing architecture

- **Eclipse Detection Engine** (systemd timer, from the Linux mapping) computes F each tick and emits it on D-Bus.
- The **Universe Scheduler** (control plane) reads F, applies the regime and the budget caps, and decides how many Moon Universes to instantiate per axis.
- `MetricThresholdExceeded(force, value)` can reuse the existing D-Bus signal when F crosses a regime boundary.
- **Observatory** (Prometheus/OpenTelemetry) graphs F over time — the universe's heartbeat of ambition.

## What this deliberately leaves out (and why)

- **No learning weights yet.** A future version could tune the weights from promotion success rates (universes that produced good promotions teach the system which signals predicted them). That's the "hallucinations of math" becoming experience — correctly sequenced *after* the prototype works.
- **No per-galaxy force.** This spec computes one universe-wide number. Per-galaxy force is a natural v2, once galaxies are first-class objects in the 0.1 prototype.
- **No merge-quality feedback into F.** Merge outcomes feed the Consensus Engine, not this function — keeping the force function about *whether to experiment*, not *whether experiments succeeded*.

## Open questions for Jordan

1. **Weights:** does 0.20 for eclipse state and twinkle density feel right, or should something else vote louder?
2. **The Convergence gate:** require R ≥ 0.95 (strict — anchors near-perfect), or allow Convergence at lower anchor trust with fewer universes?
3. **Ceilings:** is 5,000 twinkles/tick the right "maximum" for normalization, or should the ceiling be higher?

*Provenance: formalizes Jordan's Convergence Eclipse note (2026-10-09) and the Afterburner triad — gravity reveals what exists, dark matter reveals why, antigravity reveals what could exist. Fulfills the open offer from 2026-10-09 to formalize the force function as a computable spec.*
