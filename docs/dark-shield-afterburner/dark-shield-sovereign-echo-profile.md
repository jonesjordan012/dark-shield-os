# Sovereign Echo Profile — mapping AB-8's four contents onto the Echo Schema

*Draft v0.1 by Muse, 2026-10-12, at Jordan's request. **Ruled by Jordan 2026-10-12 — now canon.** All three judgment calls upheld; the false-attestation question ruled.*

## Purpose

The Echo Schema Specification defines the general record. This profile specializes it for **AB-8 All Systems Go sessions**: it states exactly where each of the sovereign echo's four contents lives in the schema, which fields are fixed, and which special rules apply.

## The mapping

| AB-8 content | Schema home | How |
|---|---|---|
| **Perceptual record** — what the Citizen saw | Evidence layer | One or more `EvidenceReference`s with `source: npu-prosthesis-render`, capturing the prosthesis state at session time: time made evident, hallucination rendered on UI, critical metrics visible, Dark Shield seen as protectorate. Answers: *in what light did they act?* |
| **Deed trace** — what the Citizen did | Claim + Evidence layers | The Echo's `claim.statement` declares the session itself ("Citizen exercised bare-metal authority, session S"). Every bare-metal command becomes an ordered `EvidenceReference` (`source: deed-log`, recording command, target, effect, timestamp). Nothing touched leaves no mark. |
| **Plausibility context** — why the hands moved | Confidence layer | A `ConfidenceRecord` with `generated_by: {actor: NPU, method: plausibility-designation}`, `rationale` citing the designated twinkling-star mind-map pattern — or the recovery flag: `"recovery — no pattern, universe broken"`. This is what the confidence `origin` field exists for. |
| **Anchor delta** — what the anchors looked like before and after | Witness layer + Evidence | Each Anchor emits a `WitnessRecord` (`attestation: observed`, NPU co-signature) over an `EvidenceReference` holding the before/after state. The bypass itself is recorded as evidence — the anchor is not silent about being bypassed. |

## Fixed fields

- `created_by`: the Citizen's ActorID. The sovereign echo is always authored by the sovereign whose hands moved.
- `subject.type`: `"ab8-session"`. `subject.id`: the session UUID.
- `witnesses`: MUST include the NPU signature (truthfulness of the record) and one `WitnessRecord` per Reality Anchor (the delta). No sovereign echo is valid without both.
- `claim.declared_by`: the Citizen. `claim.declared_at`: the moment All Systems Go was engaged.

## Special rules (ruled by Jordan, 2026-10-12)

1. **Write-once.** A sovereign echo is never updated. Correction happens only through `Revision` lineage — and see rule 2.
2. **Succeeded, never superseded.** *Sovereign Echoes may be succeeded. Sovereign Echoes may not be superseded.* A sovereign Echo is a historical event, not a mutable conclusion: confidence records may be superseded, interpretations revised, doubts resolved — but the Echo records that a constitutionally recognized act entered memory, and that stands forever. Later acts create *successor* Echoes, linked as followed-by, never superseded-by:
   ```
   Echo A → followed by Echo B     (not: superseded by)
   ```
3. **The recognition chain, applied.** Designation (NPU pattern or recovery flag) → Declaration (Citizen engages All Systems Go) → Witness (NPU signature + anchor attestations) → Echo (this record) → Inspection (per the Access Rule). Break the chain and constitutional recognition fails: the event may have occurred, the command executed, the machine changed — but constitutional memory is not merely occurrence. *Constitutional memory is witnessed occurrence.* An unwitnessed event happened; an unwitnessed sovereign act did not happen *here*.
4. **Access.** Governed entirely by the Sovereign Echo Access Rule (canon 2026-10-12): Citizen unrestricted, Anchors trusted-history, all others by explicit delegation only, Moons never directly. The schema carries no access fields; implementations MUST enforce the Rule alongside the schema.
5. **False witness becomes part of memory.** *Falsification creates a successor Echo. Falsification does not erase an existing Echo.* If an attestation is later discovered false, the original Echo stands — the universe must remember that it was once deceived; the memory of the deception matters more than the correction. The new Echo records the falsification, references the original via lineage, and both remain visible. *The universe does not preserve correctness. The universe preserves provenance.* Correctness may change, meaning may change, confidence may change — what must never disappear is the answer to "where did you come from?", even when the answer is "I came from a mistake."

## Clarifications (ruled by Jordan, 2026-10-12)

- **`generated_by` is attribution, not ownership — normative.** Conceptually the field is `attributed_to`, even where implementations retain the existing field name. *Attribution identifies source. Attribution does not imply authority.* No actor owns: confidence, plausibility, interpretation validity, truth. Actors own only: actions, attestations, perspectives.
- **Status at two levels.** Echo-level `status` governs the record as a whole (for sovereign echoes: always active, never superseded — see rule 2). Per-record statuses (doubt, interpretation) govern components *within* an active echo. An active sovereign echo may carry resolved doubts and revised interpretations; it may never itself become `superseded`.

## Open questions for Jordan

*All three judgment calls and the false-attestation question are ruled. No open questions remain on this profile.*

*Provenance: drafted by Muse 2026-10-12 from Jordan's Echo Schema Specification (2026-10-12), the All Systems Go Echo draft and Sovereign Echo Access Rule (2026-10-12), and the AB-8 canon. **Ruled by Jordan 2026-10-12**: all three judgment calls upheld (succeeded-never-superseded with followed-by lineage; missing witness fails recognition — "constitutional memory is witnessed occurrence"; generated_by strengthened to normative attribution language with the ownership inventory), and the false-attestation question ruled (false witness becomes part of memory; falsification creates a successor Echo; "the universe does not preserve correctness, it preserves provenance").*
