---
name: ue-reference-engine-source
description: Use BEFORE writing any new UE feature (especially UI / Editor / Asset Editor / Slate / Localization / SourceControl / Validator / Subsystem / Factory / Details Customization) — first locate and read the closest reference implementation in UE engine source / official samples, because the UE framework is largely undocumented and correct patterns live in engine source, not API docs. Provides a 5-tier reference-priority list + a table indexed by ~22 UE subsystems pointing at the right engine-source files. Symmetric counterpart to `reuse-before-implementing` (project-internal survey). Skip for non-UE work.
---

# UE Reference Engine Source

Meta prep-work rule for UE work: **before implementing any UE framework feature, locate the closest reference implementation and read it first.**

UE framework is largely undocumented. Correct usage patterns, implicit contracts, and call-order requirements live in engine source / official samples, not in API doc comments or web tutorials.

The full content lives in the bundled doc:

[`reference-engine-source.md`](reference-engine-source.md) — 5-tier priority order, categorized reference table indexed by ~22 UE subsystems, official sample projects, search keyword patterns, 4 anti-patterns, and 11 project-validated examples.

## When This Fires

| Trigger | Reason to read engine source first |
|---|---|
| Authoring new `UEdGraph` / `Schema` / `SGraphNode` | Each has 10+ implicit contracts (NodeGuid init, Pin SetOwner, RF_Transactional, factory registration) only visible in engine source |
| Authoring new `UAssetDefinition` / `Factory` / `Validator` / `Subsystem` | Framework expectations (e.g. `CanDuplicate` coverage scope) are not in docs |
| Implementing Slate widget / Details Customization | Reference impl is the only way to learn correct `SetOwner` / `OnFinishedChangingProperties` / etc. usage |
| Overriding any UE virtual method for the first time | Call order + side effects are encoded in engine usage, not doc comments |
| Diagnosing crash / weird behavior | Engine source shows how UE intends the feature to work — your reproduction often deviates from intended usage |
| Reviewing AI-generated UE code | Every API used must be grep-verified against current engine version (AI training data often stops at older UE versions) |

## How to Apply

1. **Pre-action**: open the bundled `reference-engine-source.md` and find the row in the "按 UE 子系统分类的 reference 清单" table matching what you are building. The right column lists the engine source files to read.
2. **For unfamiliar features**: pick the simplest reference impl first (e.g. `SGraphNodeKnot` before `SGraphNodeK2Default`).
3. **Cross-check**: when two reference impls differ, the constraint is weak / it's a style choice — pick the one closest to your context.
4. **Never copy blind**: read for the implicit contracts ("why does this `check()` exist?"), then implement in your own naming / data model.

## Pair With

- `guidelines/code/reuse-before-implementing.md` — symmetric prep-work for project-internal code survey (UE engine vs project repo are two different "what already exists" searches; do both before writing new code).
- `skills/ue/ue-module-architecture/SKILL.md` — module / layer decisions often happen at the same prep stage as reference lookup.
- `techniques/ue-custom-graph-editor.md` — procedural application for graph editor work; its "Prerequisites" section is this skill applied to one specific subsystem.

## Anti-Pattern Summary

Full list in bundled doc. The four most common:

1. "I assumed UE works this way" — most frequent bug source; cure is forcing a 30-minute reference read before coding.
2. Trusting AI-generated UE code without grep-verifying against current engine version.
3. Copy-pasting forum workarounds without reading engine source to understand root cause.
4. Pushing past "no reference found" — if no engine source / sample / forum post exists for what you want, you are likely using the wrong path; redesign rather than force it.
