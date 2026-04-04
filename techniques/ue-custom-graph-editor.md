# Building a Custom Graph Editor in UE

## Purpose

Step-by-step procedure for creating a custom node-graph editor (similar to Blueprint,
Material Editor, or Behavior Tree) inside an Unreal Engine plugin. Each step includes
the key pitfalls and a verification checkpoint.

## Prerequisites

- Read the closest UE reference implementation before writing code. Good starting points:
  - **Animation State Machine**: `AnimationStateMachineGraph.h`, `AnimationStateMachineSchema.h`
  - **Material Editor**: `MaterialGraph.h`, `MaterialGraphSchema.h`
  - **Behavior Tree**: `BehaviorTreeGraph.h`, `BehaviorTreeGraphNode.h`
- Do not implement from guesswork. UE's graph framework has many implicit contracts
  that are only visible in existing implementations.

## Step 1 — Define Runtime Data Model

Create the runtime node classes as plain `UObject` subclasses. These represent the
domain data and must not depend on any Editor module.

```
MyRuntimeNode : UObject
├── Properties relevant to gameplay / runtime logic
└── No UEdGraph*, no UEdGraphNode*, no Editor #includes
```

**Verification**: the Runtime module compiles with `Editor` excluded from its
`Build.cs` dependencies.

## Step 2 — Define the Asset Class

Create a `UObject`-derived asset that owns the runtime data.

```cpp
UCLASS()
class UMyGraphAsset : public UObject
{
    UPROPERTY()
    TArray<TObjectPtr<UMyRuntimeNode>> Nodes;

#if WITH_EDITORONLY_DATA
    UPROPERTY()
    TObjectPtr<UEdGraph> EdGraph;
#endif
};
```

- The `UEdGraph*` lives under `WITH_EDITORONLY_DATA` so it is stripped in cooked builds.
- Register an `UFactory` subclass so the asset can be created from the Content Browser.

**Verification**: create the asset in the Content Browser. It should appear and save
without errors.

## Step 3 — Create Editor Module + UEdGraphNode Subclass

Create an Editor module (separate from the Runtime module). Define a `UEdGraphNode`
subclass that wraps the runtime node.

```cpp
UCLASS()
class UMyEdGraphNode : public UEdGraphNode
{
    UPROPERTY()
    TObjectPtr<UMyRuntimeNode> RuntimeNode;

    virtual void AllocateDefaultPins() override;
};
```

**Critical**: in any code that creates instances of this node, call:
```cpp
Node->CreateNewGuid();
Node->PostPlacedNewNode();
```
See `guidelines/ue/graph-editor-constraints.md` — NodeGuid Initialization.

**Verification**: create a node programmatically, inspect `Node->NodeGuid` — it must
be non-zero.

## Step 4 — Implement UEdGraphSchema

Subclass `UEdGraphSchema` to define:

| Override | Purpose |
|----------|---------|
| `GetGraphContextActions` | Populates the right-click "Add Node" menu |
| `CanCreateConnection` | Rules for which pins can connect |
| `TryCreateConnection` | Executes a connection between two pins |
| `CreateDefaultNodesForGraph` | Creates the initial node(s) when a new graph is opened |

**Critical**: in `FEdGraphSchemaAction::PerformAction`, if `FromPin != nullptr`,
manually call `TryCreateConnection`. See `guidelines/ue/graph-editor-constraints.md`
— Pin Auto-Connection.

**Verification**: right-click the graph → the context menu shows your node types.
Create a node from a pin drag → it connects automatically.

## Step 5 — Implement SGraphNode + Register Factory

Create a custom `SGraphNode` subclass for visual layout (pin placement, title bar,
custom widgets).

**Critical**: register a `FGraphPanelNodeFactory` in the Editor module's
`StartupModule()` and unregister in `ShutdownModule()`. See
`guidelines/ue/graph-editor-constraints.md` — Custom SGraphNode Factory Registration.

**Critical**: call `PinWidget->SetOwner()` only once, inside `AddPin()`. See
`guidelines/ue/graph-editor-constraints.md` — Pin Ownership.

**Verification**: open the graph editor. Nodes should render with your custom layout,
not the default Blueprint-style box.

## Step 6 — Create the Asset Editor (Toolkit)

Create a `FAssetEditorToolkit` (or `FWorkflowCentricApplication` for tab-based
layouts) that hosts the `SGraphEditor` widget.

```cpp
// In your toolkit's InitEditor:
SNew(SGraphEditor)
    .GraphToEdit(MyAsset->EdGraph)
    .GraphEvents(/* your event delegates */)
```

Key setup:
- Bind `OnSelectionChanged` to update a details panel.
- Bind `OnNodeDoubleClicked` if nodes should open sub-editors.
- Wire undo/redo commands to `GEditor->Trans->Undo()` / `Redo()`.

**Verification**: double-click the asset in Content Browser → the editor opens with
an empty or default-populated graph. Undo/redo work for node creation and deletion.

## Step 7 — Register Asset Type Actions

Register `IAssetTypeActions` (or use `UAssetDefinitionDefault` in UE 5.x) so the
Content Browser knows how to handle the asset:

- Double-click → opens your toolkit.
- Right-click → "Create New" shows your asset type.
- Correct color and icon in the browser.

**Verification**: Content Browser shows correct icon and color. Double-click opens
the custom editor. Right-click → Create works.

## Post-Setup Reminders

- **Cold rebuild** after any C++ graph editor change. Do not rely on Live Coding.
  See `guidelines/ue/graph-editor-constraints.md` — Cold Rebuild Over Live Coding.
- **Validate against a real test asset** — compile success alone does not confirm
  correct graph behavior. See `guidelines/code/validation.md` — Graph/Blueprint Commands.
- When adding editing operations, follow the editor/runtime separation principles
  in `guidelines/ue/editor-runtime-separation.md`.

## Related Guidelines

- `guidelines/ue/graph-editor-constraints.md` — hard constraints referenced throughout.
- `guidelines/ue/editor-runtime-separation.md` — operation layering for undo support.
- `guidelines/code/validation.md` — general validation principles.
