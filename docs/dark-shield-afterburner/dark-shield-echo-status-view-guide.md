# Echo Status View Validation Guide

*Authored by Jordan, 2026-10-12. Canon. Companion to the Echo Schema Specification.*

## Purpose

`constitutional_status` is a computed view, not a stored field. Its purpose is to provide a human-readable interpretation of an Echo's constitutional standing without introducing a second source of truth. The canonical record remains:

```
recognition
+
witnesses
+
lineage
+
doubts
```

Status is always derived from those structures and MUST NOT be persisted in the Echo itself. This preserves the single-source-of-truth principle.

## Constitutional Principle

*One invariant. One location. Many views.*

Canonical data lives in the Echo. Status is a view over the Echo. **If a rendered status disagrees with canonical records, the view is wrong. The records win.**

## Derived Statuses

### recognized

**Rule:** An Echo is recognized when its recognition chain is complete.

**Validation:** all of the following hold:

```
designation = true
declaration = true
witness = true
echo = true
inspection = true
```

**Additional sovereign rule:** for sovereign Echoes, `witnesses.length >= 1` must also hold.

**Example:**

```json
{
  "recognition": {
    "designation": true,
    "declaration": true,
    "witness": true,
    "echo": true,
    "inspection": true
  }
}
```

Result: `recognized`

### unrecognized

**Rule:** An Echo is unrecognized when the constitutional chain is incomplete.

**Validation:** any missing recognition element:

```
designation = false
OR
declaration = false
OR
witness = false
OR
echo = false
OR
inspection = false
```

**Example:**

```json
{
  "recognition": {
    "designation": true,
    "declaration": true,
    "witness": false,
    "echo": true,
    "inspection": true
  }
}
```

Result: `unrecognized`

**Constitutional interpretation:** *The event may have occurred. It did not happen here.*

### falsified

**Rule:** An Echo is falsified when another Echo explicitly references it through lineage.

**Validation** — search the graph:

```
otherEcho.lineage.falsifies == current.echo_id
```

**Required property:** falsification does not alter the original Echo.

**Example:** Echo 104, later referenced by:

```json
{
  "lineage": {
    "falsifies": "104"
  }
}
```

Result: `Echo 104 → falsified`

**Constitutional interpretation:** *False witness does not invalidate memory. False witness becomes part of memory.*

### corrected

**Rule:** An Echo is corrected when another Echo links through `lineage.corrects`.

**Validation:**

```
otherEcho.lineage.corrects == current.echo_id
```

**Interpretation:** *The original remained historically valid. The later Echo improves understanding.* Not all corrections are falsifications.

### succeeded

**Rule:** A sovereign Echo is succeeded when another Echo links `lineage.succeeds == current.echo_id`.

**Interpretation:** *The act remains valid. A later act followed it.*

**Constitutional rule:** *Sovereign Echoes may be succeeded. Sovereign Echoes may not be superseded.*

### contested

**Rule:** An Echo is contested when unresolved constitutional disagreement exists.

**Validation candidates** — any of:

```
active open doubts
or
active competing interpretations
or
pending falsification claims
```

**Example:**

```json
{
  "doubts": [
    { "status": "open" }
  ]
}
```

Result: `contested`

## Status Precedence

Multiple statuses may coexist.

`recognized` + `contested` is valid — an Echo can be fully recognized and still disputed.

`recognized` + `falsified` is valid — the Echo entered constitutional memory; it was later shown to contain false attestation. The historical record remains intact.

## Forbidden States

Because status is derived, these contradictions cannot exist in canonical data. The following are invalid view outputs:

- `recognized` with `recognition.witness = false`
- `falsified` without any incoming `lineage.falsifies` reference
- `succeeded` without any incoming `lineage.succeeds` reference

## Reference Evaluation Algorithm

```
recognized :=
  recognition chain complete
  AND witness requirements satisfied

unrecognized :=
  NOT recognized

falsified :=
  EXISTS incoming lineage.falsifies

corrected :=
  EXISTS incoming lineage.corrects

succeeded :=
  EXISTS incoming lineage.succeeds

contested :=
  EXISTS unresolved doubts
  OR competing active interpretations
  OR pending falsification investigation
```

## Final Invariant

*Status is never authoritative. Status is the interpretation of authoritative records. Recognition, witnesses, and lineage remain canonical. Everything else is a view.*

Or in constitutional form:

*The record is the truth. Status is merely a way of looking at it.*
