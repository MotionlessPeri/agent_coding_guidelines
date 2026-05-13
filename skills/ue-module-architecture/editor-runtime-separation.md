# Editor / Runtime Separation

## Core Principle

Separate graph and asset operations into layers so that domain logic is reusable at
runtime and editor operations carry proper undo/dirty-marking support.

## Three-Layer Model

| Layer | Responsibility | Module | Depends on Editor? |
|-------|---------------|--------|--------------------|
| **Runtime Ops** | Constraint validation, data mutation, structural queries | Runtime | No |
| **Editor Actions** | Wrap Runtime Ops with `FScopedTransaction`, `Modify()`, `MarkPackageDirty()`, UI notifications | Editor | Yes |
| **UI** | Calls Editor Actions only — never manipulates data directly | Editor | Yes |

- Runtime Ops must compile without any Editor module dependency.
- Editor Actions are thin wrappers: they add undo support and dirtying, then delegate
  to the corresponding Runtime Op.
- UI code (detail panels, toolbars, graph interactions) calls Editor Actions, never
  Runtime Ops directly.

## When to Introduce This Layering

Introduce the three-layer split when:
- The asset has more than ~5 distinct editing operations, **and**
- Operations involve constraint validation or complex interactions (drag-and-drop,
  multi-object edits, conditional rules).
- Runtime code also needs to modify the data (procedural generation, gameplay-time
  mutation).

## Simpler Alternative

For assets with few operations and no runtime mutation needs, skip the layering.
Use the minimal undo pattern directly in UI code:

```cpp
const FScopedTransaction Transaction(NSLOCTEXT("MyEditor", "EditFoo", "Edit Foo"));
Object->Modify();
// ... modify properties ...
Object->MarkPackageDirty();
```

This is sufficient when the operation count is small and there is no need to share
logic with runtime.

## Undo Support

### Basic Pattern

Always wrap data modifications in `FScopedTransaction` + `Modify()`:
1. Create `FScopedTransaction` — this opens an undo group.
2. Call `Object->Modify()` — this snapshots the object for undo.
3. Perform the mutation.
4. Call `Object->MarkPackageDirty()` — this marks the package as needing save.

### Nested Transactions (Drag Scenarios)

- `MouseDown` / `DragStart`: create an outer `FScopedTransaction`.
- `MouseMove` / `DragUpdate`: inner Editor Actions create their own
  `FScopedTransaction`. UE automatically merges nested transactions into a single
  undo step.
- `MouseUp` / `DragEnd`: the outer transaction scope closes.

This produces one undo entry for the entire drag operation, even though multiple
intermediate mutations occurred.

## Automating Editor Action Generation

Editor Actions are mechanical wrappers — each one follows the same
`Transaction → Modify → call Runtime Op → MarkPackageDirty` pattern. When the
operation count grows, hand-writing these wrappers becomes tedious and error-prone
(easy to forget `Modify()` or use the wrong transaction description).

### ExecEditorOp — Centralizing the Wrapper Logic

Before automating generation, first extract the shared boilerplate into a single
template function. All Editor Actions (hand-written or generated) delegate to it:

```cpp
template<typename OpFunc>
static bool ExecEditorOp(FMyViewModel& VM, const FText& Desc, OpFunc Op)
{
    UMyAsset* Asset = VM.GetAsset();
    if (!IsValid(Asset)) return false;

    FScopedTransaction Transaction(Desc);

    FText Error;
    const bool bSuccess = Op(Asset, &Error);

    if (bSuccess)
    {
        Asset->PostEditChange();
        Asset->MarkPackageDirty();
        VM.NotifyModelChanged();  // trigger UI refresh
    }
    else
    {
        UE_LOG(LogMyEditor, Warning, TEXT("%s failed: %s"),
            *Desc.ToString(), *Error.ToString());
    }
    return bSuccess;
}
```

Key design points:
- `ExecEditorOp` is hand-written and lives in the Editor Actions header.
- It centralizes Transaction, post-edit notifications, dirty marking, error logging,
  and ViewModel observer notification in one place.
- Runtime Ops receive the raw asset and an optional `FText* OutError`; they call
  `Asset->Modify()` internally before mutating data.
- The lambda captures the middle parameters and forwards them to the Runtime Op.

### Automation Approaches

Consider automating the generation of Editor Action wrappers:

- **C++ macro / template approach**: for each Editor Action, write a one-liner that
  names the Runtime Op and its parameters. Keeps everything in C++ with no external
  tooling. Sufficient when operations are few and signatures are uniform.

- **Python codegen script**: parse the Runtime Ops header, extract public static
  function signatures, and emit Editor Action `.h` / `.cpp` files. This approach
  scales well and can also extract LOCTEXT descriptions from Doxygen comments
  automatically. Proven pattern for 7+ operations.

- **UE reflection / metadata**: tag Runtime Ops with `UFUNCTION` metadata, then write
  a utility that iterates reflected functions to generate or dispatch Editor Actions
  at runtime. More dynamic but adds complexity.

### Codegen Architecture (Python Script Pattern)

When using a Python codegen script, the recommended file organization:

```
EditorModule/
├── Public/
│   ├── MyEditorActions.h           ← hand-written: ExecEditorOp + special helpers
│   └── MyEditorActions.codegen.h   ← generated: wrapper declarations
├── Private/
│   └── MyEditorActions_Codegen.cpp ← generated: wrapper implementations
```

**How to include generated declarations**: the hand-written header `#include`s the
`.codegen.h` inside the class body:

```cpp
class FMyEditorActions
{
public:
    // Hand-written: the ExecEditorOp template
    template<typename OpFunc>
    static bool ExecEditorOp(FMyViewModel& VM, const FText& Desc, OpFunc Op);

    // Hand-written: special-case helpers (e.g., clamped drag operations)
    static bool ClampedSetStartTime(FMyViewModel& VM, const FGuid& Id, float Time);

    // Generated wrappers — one per Runtime Op
    #include "MyEditorActions.codegen.h"
};
```

**Signature transformation**: the script transforms Runtime Op signatures into
Editor Action signatures:
- First param (raw asset pointer) → replaced with ViewModel reference
- Last param (`FText* OutError`) → removed (ExecEditorOp handles errors internally)
- Middle params → forwarded as-is

```
// Runtime Op signature (input):
static bool CreateBlock(UMyAsset* Asset, float Start, float End, FText* OutError);

// Generated Editor Action signature (output):
static bool CreateBlock(FMyViewModel& VM, float Start, float End);
```

**LOCTEXT from Doxygen comments**: the script extracts the first meaningful line
from each Runtime Op's `/** ... */` doc comment and uses it as the LOCTEXT value
for the transaction description. This prevents drift between code documentation
and user-visible undo strings — the Runtime Op's doc comment is the single source
of truth.

**UTF-8 BOM**: generate output files with `utf-8-sig` encoding for MSVC / UE
compatibility, especially when doc comments contain non-ASCII characters.

### Hand-Written vs Generated Split

Not everything should be generated. Keep hand-written:
- `ExecEditorOp` itself (the shared template).
- Special-case wrappers that add logic beyond the standard pattern (e.g., clamping
  values into legal ranges before calling the Runtime Op, for drag interactions).
- Operations with non-standard signatures or multi-step flows.

Generate only the mechanical 1:1 wrappers where the Editor Action does nothing
beyond calling ExecEditorOp with the corresponding Runtime Op.

### When to Automate

- 10+ operations with identical wrapper structure — codegen script pays off.
- 5–10 operations — ExecEditorOp template + hand-written one-liner wrappers is
  likely sufficient; a full codegen may be overkill.
- <5 operations — hand-write everything; the overhead of automation exceeds the savings.

**Regardless of approach**: the generated Editor Actions must still follow the same
rules (transaction before modify, constraints in Runtime Ops, etc.). Automation
removes boilerplate, not responsibility.

## Common Mistakes

- Calling `Modify()` after the mutation instead of before — undo will restore the
  already-modified state.
- Forgetting `MarkPackageDirty()` — the asset appears unchanged and won't prompt
  for save.
- Putting constraint validation in the Editor layer — makes it unavailable at runtime.
  Constraints belong in Runtime Ops.

## Related Guidelines

- See `guidelines/ue/graph-editor-constraints.md` for graph-specific rules.
- See `techniques/ue-custom-graph-editor.md` for the full graph editor setup procedure.
