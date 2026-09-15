---
name: ue-module-architecture
description: Use when designing or reviewing UE module boundaries, Build.cs dependencies, or runtime operations, editor actions, and UI layering within one module. Also use for module-related build or packaging failures. Skip non-UE work.
---

# UE Module Architecture

Two complementary rules for splitting UE plugin / project code across modules and layers.

| Scope | Rule | Content |
|---|---|---|
| **Inside one module** | Three-layer model: Runtime Ops (pure domain logic) / Editor Actions (transaction + dirty wrappers) / UI (calls Editor Actions only). Plus undo discipline, ExecEditorOp template, optional codegen. | [`editor-runtime-separation.md`](editor-runtime-separation.md) |
| **Across modules** | Runtime `*.Build.cs` MUST NOT depend on any Editor module — not even under `if (Target.bBuildEditor)`. `WITH_EDITOR` does not save you. Direction is always Runtime ← Editor, never reverse. | [`runtime-module-no-editor-dep.md`](runtime-module-no-editor-dep.md) |

The two rules operate at different scales but are typically applied together: when extracting a plugin, designing a new module, or reviewing Build.cs changes, both fire at the same decision point.

## When This Fires

- Creating a new Runtime / Editor module
- Editing any `*.Build.cs` — apply the cross-module rule
- Extracting code from a Demo project into a plugin (high-frequency trigger: every module decision)
- Adding a new class / test / setting / delegate — decide where it belongs first
- Reviewing PRs touching module boundaries
- Diagnosing cook / package failures: "missing module", unresolved-external-symbol, "Couldn't find module rules file"
- Designing the layering of a non-trivial asset editor (≥5 operations, or runtime mutation needed)

## How to Apply

1. **Pre-action**: read the two bundled docs (or the relevant one for the scope you're at — within-module vs across-modules).
2. **For Build.cs work**: walk the review checklist in `runtime-module-no-editor-dep.md` § "review checklist".
3. **For new editor operations**: decide first if the three-layer model in `editor-runtime-separation.md` applies (operation count + runtime mutation criteria), then layer accordingly.
4. **For diagnostic work**: match symptom against `runtime-module-no-editor-dep.md` § "怎么诊断".

## Related

- skill `ue-reference-engine-source` — engine modules' `Type` field is the authoritative reference for "is this module editor-only" (grep `<ModuleName>.Build.cs` in engine source)
- `guidelines/ue/graph-editor-constraints.md` — graph-specific rules that often interact with the layering decision
- skill `ue-custom-graph-editor` — procedural guide that applies the three-layer model in graph editor context
