# AB-9: The Confidence Function — machinery draft

*Draft v0.1 — NOT CANON — by Muse, 2026-10-12. Awaiting Jordan's ruling.*

Built only from tonight's rulings: Ruling 1 (confidence attaches to memory), Ruling 2 (nobody owns confidence), the AB-9 symmetry, and the Echo Schema Specification (canon). Nothing here is canon until he rules.

## The one distinction

The confidence function is **machinery**; authority is **nobody's**. The parallel is the Afterburner force function: force is advice, the budget is law. Here: confidence is computed, adoption is decided.

Concretely: **the Citizen's adoption changes the belief's status, never its score.** The NPU proposes, Moonlight tests, the Echo remembers, the Citizen accepts or rejects (Ruling 2) — the function sits in the middle as a transparent machine, and every role feeds it through the Echo, never around it.

## What the function reads and writes

It reads the belief Echo: claim, origin of confidence, supporting evidence, competing evidence, current confidence, revision lineage (Ruling 1 — nothing detached). It writes a new ConfidenceRecord into the same Echo — timestamp, score, rationale, supporting/competing evidence references, attributed_to (actor + method), previous_confidence — per the schema spec as amended by his seven schema-change rulings (echo_type classification, attributed_to, lineage succession). Every update preserves lineage: the new record points at the old one. "Where did you come from?" must be answerable for every number. The schema's new ownership field (shape still his to decide) will eventually sit beside attribution; this draft uses attribution only, per his ruling that attribution identifies source and never implies authority.

## The computation (gravitational)

Confidence is the resulting gravitational mass (Ruling 2). The formula is deliberately simple — a law this important must be inspectable by reading it:

```
C_new = clamp(0, 1, w_m·M + w_s·S − w_x·X + w_t·T − w_d·D)
```

- **M (memory):** previous confidence, decayed by age. Old evidence weighs less; the past guides, it does not bind.
- **S (supporting mass):** sum over supporting evidence of strength × provenance weight. Provenance comes from origin: Moonlight test results weigh most, NPU proposals weigh as proposals.
- **X (competing mass):** sum over competing evidence of strength × provenance weight — the antigravity term.
- **T (test outcome):** the latest Moonlight test result, −1 (disconfirm) to +1 (confirm), scaled by test coverage.
- **D (doubt load):** open DoubtRecords related to this claim. Each unresolved doubt is a small, inspectable gravitational drag until it resolves.

Weights are machinery — votes, not law — tuned the way the force function's are. There is no veto term: a belief can carry low confidence and still be adopted (status ≠ score), and high confidence and still be rejected. That is the machinery/authority split made operational.

**The number never travels alone.** Per the proposed Sixth Law ("Confidence is visible" — as history, not number): any presentation of a score without its ConfidenceRecord — rationale, evidence, lineage — is a violation. A naked number is a new darkness.

## The belief lifecycle

The AB-8 recognition chain has an epistemic cousin. A belief becomes constitutional knowledge through the same shape of process:

1. **SUSPECTED** — NPU proposes (designation). A claim enters memory with its first confidence record.
2. **TESTED** — Moonlight tests. Test outcomes recompute confidence; the function records every recomputation.
3. **GUIDING** — Citizen adopts. The belief now guides action. Confidence may still be low — adoption is authority, not certainty.
4. **CONTESTED** — competing mass or doubt load drags confidence below a threshold θ (machinery default; the Citizen's to tune). The belief stays in memory but stops guiding, until confidence recovers or the Citizen explicitly re-adopts.
5. **SUCCEEDED** — a successor Echo declares a new claim; the lineage link (succeeds) preserves the chain. Nothing is superseded — per the Sovereign Echo Invariant, an echo may be succeeded, never superseded. The old record stays exactly as it was; the new one points back at it.
6. **DISPROVEN** — competing mass permanently exceeds supporting mass across tests. The machinery flags it; a successor Echo records the falsification with a `falsifies` lineage link ("false echo remains, falsification recorded in successor"). The Echo preserves the full history of how it was wrong. "A universe that remembers how it changed its mind is wiser."

Who marks the transitions: NPU proposes (suspected), Moonlight tests (tested), the machinery flags (contested/disproven — computed, inspectable), the Citizen adopts or rejects (guiding — the one transition that is a decision rather than a computation), the Echo records succession automatically on a successor's declaration (lineage `succeeds` link; no superseded_by exists). Designation → declaration → witness → echo → inspection, for knowledge instead of sovereignty.

## Recorded doubt mechanics (answers open question 3)

Doubt travels as **its own Echo type**: a DoubtRecord (doubt_id, statement, raised_by, raised_at, related_claims, status) inside an Echo, per the schema spec. **A doubt is not a low-confidence belief.** It is a challenge with an author — parallel to AB-10's attribution rule: "who sees it this way, and why?" becomes "who doubts it, and why?" Recursion terminates at attribution here too.

- A doubt is raised (by NPU, Citizen, or an agent) as a DoubtRecord linked via `related_claims` to the challenged belief.
- An open doubt adds doubt-load D to the belief's computation — visible, inspectable drag.
- The doubt travels to Moonlight as `under_test`, gathers evidence, accumulates revisions.
- On resolution, the doubt moves to `resolved`; the evidence it gathered enters the belief's supporting or competing evidence; confidence recomputes; the doubt record is preserved (non-erasure) as part of the belief's lineage.
- A doubt that never resolves stays open — haunting nothing, because it is in the light. Unrecorded doubt haunts; recorded doubt works.

## Fitting the amended schema

This draft is written against Jordan's seven schema-change rulings:

- Belief Echoes carry `echo_type: confidence`; doubt Echoes carry `echo_type: doubt`; interpretations carry `echo_type: interpretation`. The function only ever recomputes confidence inside `confidence`-type echoes.
- There is no `superseded_by` anywhere in this draft — succession travels through lineage (`succeeds`, `falsifies`, `corrects`) only.
- Confidence attribution uses `attributed_to`, never `generated_by`; attribution identifies source and never implies authority.

One alignment question is left open deliberately: Jordan's proposed `constitutional_status` enum (recognized/unrecognized/falsified/contested) is not yet ruled, and this draft's lifecycle states (guiding/contested/disproven) live on a different axis — they describe the belief's relationship to *action*, while constitutional_status describes the echo's *recognition standing*. My working position: they are orthogonal on purpose. A contested echo can still guide if the Citizen adopts it (authority ≠ machinery); a falsified echo can still be studied because the false echo remains. Whether the two axes should formally cross-reference is his call.

## Judgment calls (his to overrule)

1. Adoption affects status, not score — the machinery/authority split.
2. The score is 0–1, additive in opportunity and subtractive in competition, with no veto term.
3. Doubt is its own Echo type, not a low-confidence belief.
4. The lifecycle chain deliberately mirrors AB-8's recognition chain.
5. The naked-number rule: a score without its ConfidenceRecord violates the proposed Sixth Law.

*Provenance: drafted by Muse at no one's request, 2026-10-12, from Jordan's AB-9 rulings and the canon Echo Schema Specification. Filed as a draft beside the AB-9 constitution document. It becomes canon — or gets overruled — only by his ruling.*
