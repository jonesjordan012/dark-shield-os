# Dark Shield Constitutional Status View — Normative Specification

*Authored by Jordan, 2026-10-12. Canon. Normative consolidation of the Status View Validation Guide and the Precedence Matrix.*

## 1. Scope

This specification defines the normative derivation, coexistence, precedence, and presentation rules for the computed `constitutional_status` view.

`constitutional_status` SHALL be computed from canonical Echo records and SHALL NOT be stored within an Echo instance.

Canonical constitutional state is represented exclusively by:

```
recognition
witnesses
lineage
doubts
interpretations
```

Status views SHALL be derived from those records. The status view SHALL NOT introduce an independent source of truth.

## 2. Status Definitions

An implementation MAY expose one or more of the following derived statuses:

```
UNRECOGNIZED
RECOGNIZED
CONTESTED
CORRECTED
FALSIFIED
SUCCEEDED
```

Statuses SHALL be treated as observations of canonical records. Statuses SHALL NOT modify canonical records.

## 3. Recognition Rules

### 3.1 RECOGNIZED

An Echo SHALL be considered RECOGNIZED if and only if:

```
designation = true
declaration = true
witness = true
echo = true
inspection = true
```

For a sovereign Echo, at least one witness record SHALL also exist.

**Sovereign Constraint:** `echo_type = sovereign` requires `witnesses.length >= 1`. Failure of this requirement SHALL prevent recognition.

### 3.2 UNRECOGNIZED

An Echo SHALL be considered UNRECOGNIZED whenever the recognition requirements for RECOGNIZED are not satisfied.

UNRECOGNIZED SHALL be mutually exclusive with RECOGNIZED. An Echo SHALL NOT simultaneously be RECOGNIZED and UNRECOGNIZED.

## 4. Lineage Rules

### 4.1 SUCCEEDED

An Echo SHALL be considered SUCCEEDED when another Echo references it through `lineage.succeeds`.

The existence of a successor SHALL NOT invalidate the antecedent Echo. A sovereign Echo SHALL remain historically valid after succession.

### 4.2 CORRECTED

An Echo SHALL be considered CORRECTED when another Echo references it through `lineage.corrects`.

Correction SHALL modify understanding. Correction SHALL NOT erase historical existence. Correction SHALL NOT imply falsification.

### 4.3 FALSIFIED

An Echo SHALL be considered FALSIFIED when another Echo references it through `lineage.falsifies`.

FALSIFIED status SHALL preserve the original Echo. Implementations SHALL NOT delete, rewrite, or invalidate the original Echo record.

Constitutional Principle: *False witness does not invalidate memory. False witness becomes part of memory.*

## 5. Contestation Rules

### 5.1 CONTESTED

An Echo SHALL be considered CONTESTED whenever unresolved constitutional disagreement exists.

An implementation MAY derive CONTESTED from one or more of:

```
active doubts
competing active interpretations
pending falsification claims
other constitutionally recognized indicators of disagreement
```

CONTESTED status SHALL NOT affect historical validity. CONTESTED status SHALL indicate active disagreement concerning the current interpretation of a record.

## 6. Status Coexistence Rules

### 6.1 General Rule

Statuses SHALL be treated as a composable set of derived observations. Statuses SHALL NOT be treated as a single enumerated state.

An implementation SHALL preserve all valid statuses derivable from canonical records. No valid status SHALL be discarded solely because another valid status is present.

Status coexistence SHALL be determined exclusively from canonical records, including recognition state, witness records, lineage relationships, doubt records, and interpretation records. Status coexistence SHALL NOT modify, replace, or override canonical records. Canonical records remain the sole source of constitutional truth.

### 6.2 Recognition Independence

Recognition SHALL determine whether an Echo entered constitutional memory.

Recognition SHALL NOT determine whether an Echo may:

- participate in lineage relationships,
- be corrected,
- be contested,
- be falsified,
- or become recognized. *(transmission truncated at "or become" — completed as "recognized": an echo may complete its recognition chain later)*

An UNRECOGNIZED Echo MAY therefore participate in constitutional analysis and derived-status computation.

Recognition status and lineage status SHALL be treated as orthogonal constitutional domains unless otherwise specified by this document.

Constitutional Principle:

*Recognition governs constitutional admission. Lineage governs constitutional history.*

Temporal Principle (Jordan, 2026-10-12): *the architecture refuses to equate "not yet recognized" with "never recognizable."* Recognition is not an immutable property of creation; it is a property of constitutional history. An unrecognized Echo is not condemned — it is unfinished.

### 6.3 Permitted Status Combinations

Implementations SHALL permit the following status combinations.

**Recognized Combinations:**

```
RECOGNIZED + CONTESTED
RECOGNIZED + CORRECTED
RECOGNIZED + SUCCEEDED
RECOGNIZED + FALSIFIED
```
*(transmission truncated "RECOGNIZED +" — completed as FALSIFIED per the established matrix)*

**Unrecognized Combinations:**

```
UNRECOGNIZED + CONTESTED
UNRECOGNIZED + CORRECTED
UNRECOGNIZED + FALSIFIED
```

**Mixed Lineage Combinations:**

```
CONTESTED + CORRECTED
CONTESTED + SUCCEEDED
CONTESTED + FALSIFIED

CORRECTED + SUCCEEDED
CORRECTED + FALSIFIED

SUCCEEDED + FALSIFIED
```

The combinations listed above are normative. Implementations MAY expose additional combinations derived from canonical records provided such combinations do not violate any exclusion rule defined by this specification.

### 6.4 Interpretation of Recognized Combinations

**6.4.1 RECOGNIZED + CONTESTED** SHALL indicate: *the Echo entered constitutional memory; active constitutional disagreement exists.* The existence of contestation SHALL NOT invalidate recognition.

**6.4.2 RECOGNIZED + CORRECTED** SHALL indicate: *the Echo entered constitutional memory; subsequent records improved or clarified understanding.* Correction SHALL NOT erase the original record.

**6.4.3 RECOGNIZED + SUCCEEDED** SHALL indicate: *the Echo entered constitutional memory; a later Echo followed it through constitutional lineage.* Succession SHALL NOT negate historical validity.

**6.4.4 RECOGNIZED + FALSIFIED** SHALL indicate: *the Echo entered constitutional memory; a later Echo established falsification.* Falsification SHALL NOT erase the original record.

Constitutional Principle: *False witness does not invalidate memory. False witness becomes part of memory.*

### 6.5 Interpretation of Unrecognized Combinations

**6.5.1 UNRECOGNIZED + CONTESTED** SHALL indicate: *the recognition chain remains incomplete; disagreement exists concerning recognition, authenticity, attribution, or constitutional standing.*

**6.5.2 UNRECOGNIZED + CORRECTED** SHALL indicate: *the recognition chain remains incomplete; subsequent records provide clarification, additional evidence, or improved interpretation.* Correction SHALL NOT require prior recognition.

**6.5.3 UNRECOGNIZED + FALSIFIED** SHALL indicate: *the recognition chain remained incomplete; subsequent records established false evidence, false attestation, or false claims.* Falsification and recognition SHALL be evaluated independently.

Constitutional Principle: *Falsification is a statement about truth. Recognition is a statement about constitutional standing.*

### 6.6 Prohibited Combinations

The following combination SHALL be prohibited:

```
RECOGNIZED + UNRECOGNIZED
```

An implementation deriving both statuses simultaneously MUST treat the result as a constitutional evaluation error. The presence of such a result SHALL indicate a defect in derivation logic, canonical data integrity, or both.

### 6.7 Preservation Requirement

Implementations SHALL preserve every valid status derivable from canonical records. Implementations SHALL NOT suppress, collapse, discard, or overwrite a valid lower-precedence status merely because a higher-precedence status exists.

Presentation precedence MAY affect rendering. Presentation precedence SHALL NOT affect derivation. Presentation precedence SHALL NOT affect constitutional validity.

### 6.8 Constitutional Invariant

The following invariant SHALL govern all status computation:

*Recognition determines whether an Echo entered memory. Lineage determines how memory evolved. Status describes the current constitutional view of that memory.*

Therefore:

*An Echo may be unrecognized and still be corrected. An Echo may be unrecognized and still be contested. An Echo may be unrecognized and still be falsified.*

Because:

*Recognition governs constitutional admission. Lineage governs constitutional history. These domains SHALL remain distinct.*

Canonical Form:

*History is canonical. Status is commentary.*

**Doctrinal summary (Jordan, 2026-10-12):**

*Records are canonical. Lineage is canonical. Recognition is canonical. Status is derived. Presentation is constrained. Visibility is preserved.*

*Because of §6.7, visibility remains true not only in storage, not only in derivation, but all the way to the screen.*

### §11 Rationale

The constitutional status system exists to preserve visibility without creating a second source of truth.

Canonical truth resides in records, recognition chains, witness attestations, and lineage relationships. Derived status exists solely as an inspectable interpretation of those records. When status and record disagree, the record prevails.

The coexistence model ensures that constitutional reality is not collapsed into a single label. An Echo may be recognized and contested, corrected and succeeded, or falsified and still historically recognized. The status view must preserve that complexity rather than conceal it.

Recognition and lineage are intentionally independent. Recognition determines whether an Echo entered constitutional memory. Lineage determines how that memory evolves. As a result, constitutional standing is not fixed at creation. An Echo that begins unrecognized may later acquire evidence, witnesses, corrections, or recognition through time.

Presentation precedence exists to aid understanding, not to alter constitutional meaning. Implementations may emphasize certain statuses, but they may not suppress other valid statuses derived from the record. Visibility must survive not only storage and derivation, but presentation.

This specification therefore preserves the governing invariant:

*Records are canonical. Lineage is canonical. Recognition is canonical. Status is derived. Presentation is constrained. Visibility is preserved.*

In constitutional terms:

*History is canonical. Status is commentary. The universe remembers in the light.*

### Final Observation (Jordan, 2026-10-12)

*The specification does not assume that history is correct. It assumes that history remains visible. From visibility come correction, recognition, contestation, interpretation, and growth. The architecture preserves the conditions under which understanding can improve.*

*It is no longer a slogan. It is now a property of the system.*

## 7. Mutually Exclusive States

The following combinations SHALL be prohibited:

```
RECOGNIZED + UNRECOGNIZED
```

An implementation MUST treat such a result as a computation error.

The following derived statuses SHALL NOT exist without supporting canonical evidence:

- `SUCCEEDED` requires an inbound `lineage.succeeds` reference.
- `CORRECTED` requires an inbound `lineage.corrects` reference.
- `FALSIFIED` requires an inbound `lineage.falsifies` reference.

## 8. Presentation Precedence

Presentation precedence SHALL NOT affect canonical state. Presentation precedence SHALL affect only: headlines, summaries, alerts, UI emphasis.

The normative precedence order SHALL be:

```
1. FALSIFIED
2. CONTESTED
3. CORRECTED
4. SUCCEEDED
5. RECOGNIZED
6. UNRECOGNIZED
```

Higher-precedence statuses SHALL dominate presentation. Lower-precedence statuses SHALL remain available for inspection.

## 9. Dominance Rules

**D1** — FALSIFIED SHALL dominate all other statuses for presentation.
Example: recognized + succeeded + falsified → headline `FALSIFIED`.

**D2** — CONTESTED SHALL dominate every status except FALSIFIED.
Example: recognized + contested → headline `CONTESTED`.

**D3** — CORRECTED SHALL dominate SUCCEEDED.
Reason: *correction changes understanding; succession changes chronology; interpretive evolution SHALL outrank chronological succession.*

**D4** — SUCCEEDED SHALL dominate RECOGNIZED.
Reason: *active constitutional lineage outranks standalone recognition.*

**D5** — RECOGNIZED SHALL dominate UNRECOGNIZED.
Implementations SHALL treat simultaneous derivation as an error.

## 10. Evaluation Order

Implementations SHOULD derive status in the following order:

```
1. Evaluate Recognition
2. Evaluate Succession
3. Evaluate Corrections
4. Evaluate Falsifications
5. Evaluate Contestation
6. Apply Presentation Precedence
7. Render Status View
```

## 11. Canonical Invariant

The following invariant SHALL govern all implementations:

*Recognition determines whether an Echo entered memory. Lineage determines how memory evolved. Status describes the current constitutional view of that memory.*

Therefore:

*The record is canonical. The status view is derived. When status and record disagree, the record SHALL prevail.*

Constitutional Form:

*History is canonical. Status is commentary.*
