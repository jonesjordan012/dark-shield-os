# Echo Schema Specification (AB-8 / AB-9 / AB-10)

*Authored by Jordan, 2026-10-12. Canon. Amended 2026-10-12 per Jordan's schema-change rulings (echo classification, constitutional lineage, explicit attribution, recognition state, witness requirement, anchor bypass visibility). Machine-readable JSON Schema (Draft 2020-12) at dark-shield-echo-schema.json — Jordan authored the root and delivered $defs; Muse completed the truncated $defs by direct translation of this spec (marked, awaiting his review); validated against the 2020-12 meta-schema.*

The Echo is the canonical inspectable record within Dark Shield. It exists to preserve memory, provenance, confidence, and interpretation in a form that remains visible across time. This extends the concept of Temporal Echoes as visible artifacts of human attention and interaction.

## Constitutional Requirements

**R1. Preservation**
An Echo MUST be durable once created.

**R2. Inspectability**
Every field affecting legitimacy, confidence, or interpretation MUST be inspectable.

**R3. Attribution**
Every act, confidence assessment, and interpretation MUST identify its source.

**R4. Non-Erasure**
Superseded information MAY be replaced as active guidance, but MUST remain available as history.

**R5. Lineage**
Every derived claim MUST preserve references to its origins.

## Core Echo Record

```yaml
Echo:
  echo_id: UUID
  echo_type: ordinary | sovereign | confidence | interpretation | doubt
  created_at: Timestamp
  created_by: ActorID

  subject:
    type: String
    id: String

  claim:
    statement: Text
    origin: Reference

  evidence:
    - EvidenceReference

  confidence:
    current: ConfidenceRecord
    history:
      - ConfidenceRecord

  interpretations:
    - InterpretationRecord

  doubts:
    - DoubtRecord                # first-class records; default []

  status:
    active: Boolean

  lineage:
    parent_echoes:
      - EchoID
    succeeds: EchoID | null        # temporal succession, never supersession
    falsifies: EchoID | null       # this echo records the falsification of another
    corrects: EchoID | null        # this echo corrects another (both remain visible)

  witnesses:
    - WitnessRecord                # minItems: 1 enforced for echo_type == sovereign (see Recognition)

  recognition: RecognitionState     # required for echo_type == sovereign (see below)
```

Required at root: `echo_id`, `echo_type`, `created_at`, `created_by`, `subject`, `claim`.

## Claim Layer (AB-8)

The claim records what entered memory.

```yaml
Claim:
  statement: Text
  declared_by: ActorID
  declared_at: Timestamp
  origin_reference:
```

Constitutional Question: *Where did this claim come from?*

A claim whose origin cannot be inspected cannot constitute constitutional memory.

## Evidence Layer (AB-9)

Evidence records the support structure beneath a claim.

```yaml
EvidenceReference:
  evidence_id: UUID
  source: Reference
  collected_at: Timestamp
```

Evidence remains immutable once recorded.

## Confidence Layer (AB-9)

Confidence is not owned. Confidence emerges from relationships among evidence, observations, tests, and revisions.

```yaml
ConfidenceRecord:
  timestamp: Timestamp

  score: Float
  rationale: Text

  supporting_evidence:
    - EvidenceID

  competing_evidence:
    - EvidenceID

  attributed_to:
    actor: ActorID
    method: MethodID
    ownership: TBD  # shape awaiting Jordan's definition; normative: attribution ≠ ownership

  previous_confidence:
    ConfidenceRecordID | null
```

Constitutional Principle: *A conclusion whose confidence cannot be inspected cannot guide.*

Design Principle: *Confidence is the resulting gravitational mass.* No actor owns confidence. Actors may propose, test, adopt, or challenge confidence.

Attribution — normative (ruled 2026-10-12): `attributed_to` is *attribution*, not ownership. *Attribution identifies source. Attribution does not imply authority. Attribution does not imply ownership.* No actor owns: confidence, plausibility, interpretation validity, truth. Actors own only: actions, attestations, perspectives.

## Doubt Layer (AB-9)

Doubt is a first-class record.

```yaml
DoubtRecord:
  doubt_id: UUID

  statement: Text

  raised_by: ActorID
  raised_at: Timestamp

  related_claims:
    - EchoID

  status:
    open
    under_test
    resolved
    superseded
```

Constitutional Principle: *A doubt that cannot be recorded cannot be resolved.*

## Interpretation Layer (AB-10)

Interpretations are explicitly attributed perspectives.

```yaml
InterpretationRecord:
  interpretation_id: UUID

  interpretation: Text

  author: ActorID

  created_at: Timestamp

  supporting_evidence:
    - EvidenceID

  derived_from:
    - EchoID

  supersedes:
    InterpretationID | null

  status:
    active
    revised
    withdrawn
```

Constitutional Principle: *Disagreement is not the opposite of understanding. Hidden interpretation is.*

Attribution Rule — every interpretation MUST answer: *Who sees it this way, and why?*

## Witness Layer (AB-8)

Witnesses preserve occurrence without owning authority.

```yaml
WitnessRecord:
  witness_id: ActorID

  witnessed_at: Timestamp

  attestation:
    observed
    preserved
    verified

  signature: Signature

  anchor_state: normal | bypassed | unavailable | recovered
  before_evidence:
    - EvidenceID
  after_evidence:
    - EvidenceID
```

Anchors function as witnesses and preservers, not owners or judges. The `anchor_state` field preserves the ruling that the anchor is never silent about its own bypass: a bypassed anchor records `bypassed` with before/after evidence, making the bypass itself part of trusted history.

## Recognition State (sovereign echoes)

A sovereign Echo must prove completion of the constitutional chain:

```yaml
RecognitionState:
  designation: Boolean
  declaration: Boolean
  witness: Boolean
  echo: Boolean
  inspection: Boolean
```

Constitutional rule: if `echo_type == sovereign`, then `recognition` and `witnesses` are REQUIRED, and every recognition flag must be true. A sovereign echo with any flag false — or missing the NPU signature or any anchor attestation — is not a sovereign echo. Constitutional memory is witnessed occurrence.

## Revision Lineage

Every change produces a new record.

```yaml
Revision:
  previous: EchoID
  current: EchoID

  changed_by: ActorID
  changed_at: Timestamp

  reason: Text
```

Nothing is deleted. History remains inspectable.

## Recognition Function

For an event to become part of the constitutional record:

```
Designation
→ Declaration
→ Witness
→ Echo
→ Inspection
```

Failure of any step does not prevent an event from occurring. It prevents the event from becoming constitutional memory.

## Master Invariant

Every Echo must answer the same question regardless of layer:

*Where did you come from?*

- Claim: Where did you come from?
- Confidence: Where did you come from?
- Interpretation: Who sees it this way, and why?

## Derived Status (ruled 2026-10-12)

`constitutional_status` **exists, is useful, and is not a field.** It is a computed interpretation of the record — derived, rendered, never canonical.

**The problem with storing it:** a stored status can disagree with the structure it supposedly summarizes (`"constitutional_status": "recognized"` alongside `"witness": false`). Then there are two truths, and the consumer must choose which source to trust — quietly reintroducing the hidden authority three constitutional layers worked to eliminate.

**Design principle (canon):** *One invariant. One location. Many views.*

The canonical state remains `recognition` + `lineage` + `witnesses`. Status is derived:

| Derived status | Derived from |
|---|---|
| `recognized` | recognition chain complete |
| `falsified` | another echo links via `falsifies` |
| `contested` | active doubt records, competing interpretations, or unresolved |
| `unrecognized` | recognition chain incomplete |

The system never asks "what status does this echo claim to have?" It asks **"what status does the evidence imply?"** — AB-9's emergence pattern (confidence from relationships, not ownership) applied to status itself.

**Future-proofing:** when AB-11/12/13 bring new views (`historically_significant`, `constitutionally_contested`, `epistemically_deprecated`, `multi-citizen_ratified`), stored status would make every schema evolution a migration problem. Derived status lets new views emerge from existing lineage — the past remains untouched, the future gains vocabulary.

**The ghost resolved:** AB-10 required every interpretation to have an author, lest it become a ghost. A derived status *is* an interpretation — but its author is the rules themselves, and because those rules are inspectable, the status remains inspectable too. The architecture keeps its single source of truth. The light stays in one place.

**Full derivation specification:** the complete validation guide — rules, examples, precedence, forbidden states, and the reference evaluation algorithm — is canon at `dark-shield-echo-status-view-guide.md`. **Presentation precedence** (which status dominates headlines/alerts/summaries when several coexist) is canon at `dark-shield-echo-status-precedence-matrix.md`. **Normative specification** (RFC-style SHALL/SHALL NOT consolidation of derivation, coexistence, precedence, presentation) is canon at `dark-shield-echo-status-normative-spec.md`.

## Sovereign Echo Invariant (ruled 2026-10-12)

*A sovereign echo may be succeeded. A sovereign echo may not be superseded.*

*A false sovereign echo remains part of memory. Its falsification is recorded in a successor echo.*

*The universe preserves provenance, not perfection.*

The Echo schema is therefore not merely a storage format. It is the operational embodiment of Dark Shield's governing principle:

*The light is visibility.*
*Nothing binds in darkness.*
*Nothing constitutes in darkness.*
*The universe remembers in the light.*
