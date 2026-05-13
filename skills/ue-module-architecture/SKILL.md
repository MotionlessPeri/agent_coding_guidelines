---
name: ue-module-architecture
description: Hard rules for splitting UE plugin code across Runtime and Editor modules. Bundles two complementary layers — (1) within-module three-layer model (Runtime Ops / Editor Actions / UI) with proper undo / dirty-mark support, optional ExecEditorOp template + codegen, and (2) cross-module dependency direction (Runtime `*.Build.cs` can NEVER depend on Editor modules, not even under `if (Target.bBuildEditor)` — `WITH_EDITOR` won't save you; common pitfall triggers + correct redesigns). Use when designing a new UE module / plugin, when extracting a plugin out of a project, when authoring or reviewing any `*.Build.cs`, when deciding which module a new class / test / setting / delegate belongs to, or when diagnosing cook / package failures with "missing module" / unresolved-external-symbol errors.
when_to_use: Fires when (1) creating or modifying any `*.Build.cs` (especially `PublicDependencyModuleNames` / `PrivateDependencyModuleNames`), (2) creating new modules or extracting a plugin out of a project, (3) deciding which module a new class / test / setting / delegate / UObject belongs to, (4) reviewing PRs that touch module boundaries, (5) designing the layering inside a non-trivial asset editor (≥5 ops or runtime mutation needed), or (6) diagnosing UnrealBuildTool / cook / package failures naming missing modules or editor-only symbols. Skip for trivial single-file edits that don't touch module structure.
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
- `techniques/ue-custom-graph-editor.md` — procedural guide that applies the three-layer model in graph editor context
