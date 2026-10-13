# Constitutional Status Precedence Matrix

*Authored by Jordan, 2026-10-12. Canon. Companion to the Echo Status View Validation Guide.*

## Purpose

The status view is a derived interpretation layer computed from canonical Echo records. Canonical state remains:

```
Recognition
+ Witnesses
+ Lineage
+ Doubts
+ Interpretations
```

Status is never stored. Status is computed. A single Echo may possess multiple simultaneous statuses. The precedence matrix therefore does **not** determine which status is "true." It determines:

- Which status dominates presentation.
- Which status dominates alerts.
- Which status dominates summaries.

## Status Set

```
UNRECOGNIZED
RECOGNIZED
CONTESTED
CORRECTED
FALSIFIED
SUCCEEDED
```

## Priority Order

For display purposes only — higher priority dominates headlines; lower priority remains visible in detail views.

| Status | Priority |
|---|---|
| FALSIFIED | 6 |
| CONTESTED | 5 |
| CORRECTED | 4 |
| SUCCEEDED | 3 |
| RECOGNIZED | 2 |
| UNRECOGNIZED | 1 |

## Coexistence Matrix

| Status A | Status B | Allowed | Result |
|---|---|---|---|
| RECOGNIZED | CONTESTED | Yes | Recognized, under dispute |
| RECOGNIZED | CORRECTED | Yes | Recognized, later clarified |
| RECOGNIZED | SUCCEEDED | Yes | Recognized, later followed |
| RECOGNIZED | FALSIFIED | Yes | Recognized, later disproven |
| UNRECOGNIZED | CONTESTED | Yes | Contested recognition |
| UNRECOGNIZED | CORRECTED | Rare | Possible |
| UNRECOGNIZED | SUCCEEDED | No | Invalid lineage |
| UNRECOGNIZED | FALSIFIED | Yes | Failed record later disproven |
| CONTESTED | CORRECTED | Yes | Active dispute with corrections |
| CONTESTED | SUCCEEDED | Yes | Successor exists while dispute remains |
| CONTESTED | FALSIFIED | Yes | Dispute resolved toward falsification |
| CORRECTED | SUCCEEDED | Yes | Corrected then followed |
| CORRECTED | FALSIFIED | Yes | Correction escalated to falsification |
| SUCCEEDED | FALSIFIED | Yes | Historic act later falsified |

(RECOGNIZED + UNRECOGNIZED never co-occur: mutually exclusive by derivation — see D5. All 15 pairs covered.)

## Dominance Rules

**D1 — FALSIFIED dominates every other status.**
Example: recognized + succeeded + falsified → headline `FALSIFIED`; full view `recognized → succeeded → later falsified`.

**D2 — CONTESTED dominates everything except FALSIFIED.**
Example: recognized + contested → headline `CONTESTED`. Reason: *current uncertainty takes precedence over historical validity.*

**D3 — CORRECTED dominates SUCCEEDED.**
Example: recognized + succeeded + corrected → headline `CORRECTED`. Reason: *correction modifies interpretation; succession modifies chronology; interpretation outranks sequence.*

**D4 — SUCCEEDED dominates RECOGNIZED.**
Example: recognized + succeeded → headline `SUCCEEDED`. Reason: *the later constitutional act is the presently active successor.*

**D5 — RECOGNIZED dominates UNRECOGNIZED.**
Mutually exclusive by derivation. Both must never appear simultaneously.

## Valid Composite States

**Active Sovereign Record:** `RECOGNIZED` — the act entered constitutional memory.

**Historical Sovereign Chain:** `RECOGNIZED` + `SUCCEEDED` — *the act remains valid; a later act followed it.*

**Challenged Sovereign Record:** `RECOGNIZED` + `CONTESTED` — *the act entered constitutional memory; current disagreement exists.*

**Corrected Interpretation:** `RECOGNIZED` + `CORRECTED` — *the event stands; understanding evolved.*

**Falsified Attestation:** `RECOGNIZED` + `FALSIFIED` — *the event entered memory; the record later demonstrated false attestation.*

## Invalid States

These indicate computation error:

- `RECOGNIZED` + `UNRECOGNIZED` — recognition is derived from one chain.
- `SUCCEEDED` without an inbound `lineage.succeeds` reference.
- `CORRECTED` without an inbound `lineage.corrects` reference.
- `FALSIFIED` without an inbound `lineage.falsifies` reference.

## Reference Computation Order

```
1. Evaluate Recognition
2. Evaluate Succession
3. Evaluate Corrections
4. Evaluate Falsifications
5. Evaluate Active Disputes
6. Apply Dominance Rules
7. Render Status View
```

## Canonical Constitutional Interpretation

*Recognition determines whether an Echo entered memory. Lineage determines how memory evolved. Status describes the current constitutional view of that memory. The record remains primary. The status remains derived.*

Or in short form:

*History is canonical. Status is commentary.*
