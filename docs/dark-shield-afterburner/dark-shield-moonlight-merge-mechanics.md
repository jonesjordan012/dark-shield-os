# Moonlight Merge Mechanics — how the Sun takes the best from many moons

*Draft v0.1, October 11, 2026. Research prepared October 9–10, 2026, from Jordan's Moonlight design notes (2026-10-09) and his hardest open sentence — "the best traits from multiple universes can be merged" — answered and delivered October 11, 2026. The five mechanisms below are established engineering; their translation into Moonlight terms and the staging are new here. Nothing in the framing is imported from outside Jordan's design. Awaiting his review.*

## The problem in one sentence

Moon A comes home with +22% performance. Moon C comes home with a simpler galaxy. The Sun has to take **both** without breaking either.

This is the deepest open challenge in the Moonlight architecture (see `dark-shield-moonlight-spec.md` §Open questions). Consensus can *pick* the best traits — but picking is not combining. Below are five real mechanisms computers already use for exactly this, translated into Jordan's own terms, staged to match his sequencing judgment (Moonlight/Eclipse/Afterburner sequencing AFTER "plausible agency" and military-grade kernel cyber stability — see MEMORY.md).

## 1. Three-way merge — the Git move (Phase 1)

The Sun is the common ancestor; each moon is a branch off it. A merge is simply each moon's differences from the Sun, replayed together:

- Two moons touched **different stars**? The replays don't overlap — automatic, no conflict.
- Both moons touched the **same star differently**? That's a conflict — the one thing the machine cannot decide alone. Jordan resolves it by hand.

This lives natively in the **Promotion Controller**, which already does snapshot diffs. Verdict: Jordan's Phase-1 answer. Small universe, few moons, human in the loop.

## 2. Cherry-pick — trait-picking (Phase 1)

Jordan's consensus engine already thinks in *traits*, not winners. Git has a command — cherry-pick — that takes **one single change** and replays it onto a new base. That is the technical twin of his sentence: "the best traits from multiple universes can be merged."

Verdict: this should become the Consensus Engine's vocabulary. It doesn't promote moons. **It promotes traits.**

## 3. CRDTs — the deep answer (Phase 2)

CRDTs (conflict-free replicated data types) are data structures mathematically designed so concurrent edits **always converge** — no conflicts possible, no human needed. Jordan's **gravity graph** is the perfect candidate: two moons adding different relationships to the graph never truly conflict, because relationship-addition is commutative. The gravity graph merges itself.

Verdict: Phase 2. This is the deep engineering answer for when the moon count grows beyond hand-resolution.

## 4. Replay, not merge — the elegant one (Phase 2/3)

Don't merge final states — replay the winning moons' **decision histories** onto the Sun. The **Temporal Echo Recorder** already logs decisions, failures, and successes. That log *is* the replay material. The Echo Recorder stops being "history" and becomes the merge engine's memory.

A merge is just a promotion with a memory.

## 5. Version vectors — the referee (Phase 1 mechanism)

When two moons both edited the same star, the question is: did Moon B build **on** Moon A's edit (ordered — no conflict, just apply in order), or edit **independently** (true conflict)? Version vectors are how distributed systems answer that. Small mechanism, big clarity — it separates false conflicts from real ones before a human is ever asked.

## The insight that makes it Moonlight's own

**The merge itself can be tested in a Moon before it touches the Sun.** The architecture gives this for free: a merge is just another experiment — run it in a disposable moon, promote it only if it survives, with the Reality Anchors' approval as the final gate.

*Merge in a moon, promote from the moon.* The Moonlight mechanism solves its own merge problem.

## Staging

| Phase | Mechanism | Human's role |
|-------|-----------|--------------|
| 1 | Three-way merge + cherry-pick | Jordan resolves conflicts by hand |
| 2 | CRDT gravity graph | Merges run themselves for relationships |
| 3 | Per-galaxy merge policies | Rules follow *intent* — because galaxies are intentions, merge policy can be too: Development merges aggressively, Chaos results get quarantined and merge last, if at all |

## The honest limit

Structural merges can be automated. **Semantic conflicts** — two moons disagreeing on what a galaxy *means* — need understanding of intent, and that is not automatable at this layer. That is not a flaw in the design. It is why Jordan stays in the loop.

## Where it connects

- `dark-shield-moonlight-spec.md` — the architecture this resolves the open challenge of
- `dark-shield-dbus-api.md` — the `PromoteUniverse → ApprovePromotion` three-way handshake is the gate every merge passes through
- `dark-shield-moonlight-control-data-plane.md` — the Consensus Engine (trait-picking) and Temporal Echo Recorder (replay memory) already exist in this design; this doc names their merge roles
- `../dark-shield-dbus/v2/` — the frozen build contracts the merge runs on
