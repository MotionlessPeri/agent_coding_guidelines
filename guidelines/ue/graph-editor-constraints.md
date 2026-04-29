# Graph Editor Constraints

## NodeGuid Initialization

- Every newly created `UEdGraphNode` must call `CreateNewGuid()` and `PostPlacedNewNode()`
  before use.
- Failure symptom: GUID stays all-zero, `FDragConnection::ValidateGraphPinList` cannot
  resolve pins back to their owning node, and all connection dragging silently fails.
- Typical location: immediately after `NewObject<UEdGraphNode>(...)` in schema actions
  or graph factory code.

## Pin Ownership

- `PinWidget->SetOwner(OwnerWidget)` must be called exactly once per pin widget.
- The correct place is inside your `SGraphNode::AddPin()` override.
- Do not call `SetOwner` again in `CreatePinWidgets` — it triggers
  `check(!OwnerNodePtr.IsValid())` and crashes.

## Custom SGraphNode Factory Registration

- A custom `SGraphNode` subclass has no effect unless a `FGraphPanelNodeFactory` is
  registered via `FEdGraphUtilities::RegisterVisualNodeFactory`.
- Register in the Editor module's `StartupModule()`. Unregister in `ShutdownModule()`.
- Without registration, UE falls back to the default `SGraphNode`, and all custom layout,
  pin placement, and widget overrides are silently ignored.

## Pin Auto-Connection After Drag-Create

- When a user drags from an existing pin and creates a new node via a schema action,
  UE does not auto-connect the new node's pins to the source pin.
- In your `FEdGraphSchemaAction::PerformAction` override, check if `FromPin != nullptr`
  and manually call `Schema->TryCreateConnection(FromPin, CompatiblePin)`.
- If omitted, the node is placed but left unconnected — easy to miss during testing
  because the node appears correctly.

## Dynamic Pin Reconstruction

- The standard UE pattern for rebuilding pins when a property changes:
  call `ReconstructNode()` from `PostEditChangeProperty`.
- If the edited data lives on a separate `UObject` (not the `UEdGraphNode` itself),
  `PostEditChangeProperty` fires on that UObject, not on the node. Use
  `IDetailsView::OnFinishedChangingProperties()` to route the callback back to the
  owning graph node and invoke `ReconstructNode()`.
- Reference implementations: `K2Node_Switch.cpp`, `AnimGraphNode_Base.cpp`.

## Reroute / Knot Node Implementation

Implementing a reroute (knot) node in a custom graph editor requires four coordinated
pieces. Missing any one of them produces subtle visual or interaction bugs.

### 1. Widget: Inherit `SGraphNodeKnot`, do NOT override `CreatePinWidget`

- Use UE's built-in `SGraphNodeKnot` (or a thin subclass) for rendering.
- `SGraphNodeKnot` provides: 42×24 SSpacer drag handle, overlapping Input/Output pins,
  `SGraphPinKnot` with transparent Input pin and `FAmbivalentDirectionDragConnection`.
- If you override `CreatePinWidget()` and return a standard `SGraphPin`, you lose:
  transparent Input pin (both pins render → arrow icons visible), ambivalent drag
  (standard single-direction drag instead), and correct pin overlap (lines cross).
- Register the widget in your `FGraphPanelNodeFactory::CreateNode()` with a check for
  your reroute node type before falling through to your normal `SGraphNode`.

### 2. Connection Drawing Policy: No arrows + tangent flip for reroute

- The default `FConnectionDrawingPolicy` draws an arrow image at line endpoints.
  Set `ArrowImage = nullptr` in your custom policy's constructor to remove arrows.
- **Critical**: the default policy does not handle reroute tangent direction. Without
  correction, splines entering/leaving a reroute node cross each other when the
  reroute is above or below the connected nodes.
- `FKismetConnectionDrawingPolicy` solves this with `ShouldChangeTangentForKnot()`,
  but it is hardcoded to `UK2Node_Knot` casts and cannot be reused.
- In your custom policy, override `DetermineWiringStyle()`: detect reroute nodes via
  `ShouldDrawNodeAsControlPointOnly()`, compute average X position of nodes on each
  side, and flip `Params.StartDirection` / `Params.EndDirection` when the flow is
  reversed. Cache results per-node to avoid recomputation.

### 3. Schema: `OnPinConnectionDoubleCicked` for insert-on-wire

- Override `OnPinConnectionDoubleCicked` (note: UE misspells "Clicked" as "Cicked")
  to create a reroute node at the click position.
- Steps: create node, `BreakSinglePinLink` on the old connection, then
  `TryCreateConnection` twice (source→reroute, reroute→target).
- Also add the reroute to `GetGraphContextActions()` for right-click creation.

### 4. Schema: `GetPinTypeColor` for white dot appearance

- `SGraphPinKnot` renders using the schema's `GetPinTypeColor()`. The base
  `UEdGraphSchema` returns black. Override to return white (or your preferred color)
  so the knot dot is visible against the dark graph background.

## Cold Rebuild Over Live Coding

- After modifying plugin or C++ Graph Editor code, always use a cold rebuild
  (close editor → build → relaunch) instead of Live Coding.
- Live Coding frequently leaves stale widget caches, factory registrations, and
  slate state that produce behavior inconsistent with the actual code.
- Use Live Coding only for trivial, non-structural changes (string literals, log messages).

## RF_Transactional on All Graph Objects

- **Every UObject participating in undo** must have `RF_Transactional`. Without it,
  `Modify()` is silently ignored — the undo system never snapshots the object.
- This includes `UEdGraphNode` subclasses **and** any runtime data objects they
  reference (e.g. a RuntimeNode `UObject` that stores OutTransitions).
  ```cpp
  NewObject<UMyGraphNode>(ParentGraph, NAME_None, RF_Transactional);
  NewObject<UMyRuntimeNode>(Asset, NAME_None, RF_Transactional);
  ```
- `RF_Transactional` **is serialized** (it's in `RF_Load`), so once an object is
  created with it, saved assets retain the flag on load. The bug only manifests
  when creation code forgets to pass it.
- This applies to **all** creation sites: schema actions, double-click-on-wire,
  initial graph setup, MCP commands, Details panel auto-creation — anywhere
  `NewObject` is called for a graph or runtime node.
- Failure symptom: undo does not restore pin connections or runtime data.
  Nodes may disappear but wires point at removed nodes, or connections vanish.
- Blueprint nodes get this automatically via `FEdGraphSchemaAction_K2NewNode::SpawnNode`.

## Undo/Redo Must Refresh the Graph Widget

- After undo/redo, UE's transaction system restores `UEdGraph::Nodes` (removing or
  re-adding graph nodes), but **`SGraphEditor` does not automatically rebuild its
  Slate widget tree**. Stale `SGraphNode` / `SGraphPin` widgets from deleted nodes
  survive into the next render frame, and their `GetPinColor()` → `GetSchema()` →
  `GetGraph()` chain accesses a dangling Outer pointer → crash.
- Blueprint editors avoid this because `FBlueprintEditor` implements `FEditorUndoClient`
  and calls `NotifyGraphChanged()` in `PostUndo()` / `PostRedo()`.
- **Any custom graph asset editor must do the same:**
  1. Inherit `FEditorUndoClient` alongside `FAssetEditorToolkit`.
  2. Call `GEditor->RegisterForUndo(this)` in `InitEditor()`.
  3. Call `GEditor->UnregisterForUndo(this)` in the destructor.
  4. In `PostUndo()` / `PostRedo()`: call `GraphEditor->ClearSelectionSet()` and
     `GraphEditor->NotifyGraphChanged()` to force widget rebuild.
- Failure symptom: undo after node creation/paste leaves a ghost node with "(null)"
  title, followed by an access violation in `SGraphPin::GetPinColor()` or
  `SGraphPin::Tick()` on the next frame.

## Undo in Dual-Layer Data Models (Graph + Runtime)

When a custom graph editor has a separate runtime data layer (e.g. RuntimeNode with
OutTransitions) alongside the UEdGraph pin layer, **both layers must stay in sync
during undo**.

### Modify() Before Every Mutation

Every operation that modifies data must call `Modify()` on all affected objects
**before** the mutation, within an `FScopedTransaction`:

- `EdGraph->Modify()` — before adding/removing graph nodes
- `Asset->Modify()` — before adding/removing from AllNodes
- `RuntimeNode->Modify()` — before changing OutTransitions
- `GraphNode->Modify()` — before changing RuntimeNode pointer or pins

The undo system snapshots on the **first** `Modify()` call per object per
transaction. Subsequent calls in the same transaction are no-ops (safe to call).

### Use Pin Methods for Connection Changes

When rewiring connections (e.g. inserting a reroute node):

- Use `Pin->BreakLinkTo()` / `Pin->MakeLinkTo()` instead of Schema-level
  `BreakSinglePinLink()` / `TryCreateConnection()`.
- The pin methods internally call `Modify()` on owning nodes, which snapshots
  the pin `LinkedTo` arrays for undo.
- Schema-level methods additionally modify RuntimeNode OutTransitions, which
  may create undo conflicts (one object modified by two different code paths
  in ways that don't compose cleanly on undo).
- After pin-level reconnection, separately update RuntimeNode OutTransitions
  with explicit `RuntimeNode->Modify()` before each mutation.

### Delete Must Open a Transaction

`DeleteSelectedNodes()` must wrap all work in `FScopedTransaction` and call
`Modify()` on the graph, asset, and each deleted node before mutating. Use
`Pin->BreakAllPinLinks()` (which calls `Modify` internally) rather than
`Schema->BreakPinLinks()`.

## Copy/Paste Must DuplicateObject the RuntimeNode

`UEdGraphNode::PostPasteNode()` is called after `ImportNodesFromText()`.
The imported GraphNode's RuntimeNode pointer may still reference the
**original** RuntimeNode object (T3D serialization resolves object references
back to existing objects, not copies).

- Always `DuplicateObject` the RuntimeNode in `PostPasteNode()` to create an
  independent copy. Without this, paste+delete corrupts the original node's data.
- Set `RF_Transactional` on the duplicated RuntimeNode.
- Regenerate GUIDs (NodeId) on the copy and all subobjects (e.g. ChoiceItems).
- Clear OutTransitions (the framework rebuilds connections between pasted nodes).
- Do **not** call `Modify()` on the GraphNode in `PostPasteNode()` — the node
  was just created by the paste transaction. Calling `Modify()` would snapshot
  the old RuntimeNode pointer, and undo would restore it (creating a dangling
  reference to the original).
- **Do not** call `PostProcessPastedNodes()` after `ImportNodesFromText()` —
  `ImportNodesFromText` already calls `PostPasteNode()` internally. Calling
  `PostProcessPastedNodes` invokes it a second time, causing double
  `DuplicateObject` and corrupted undo state.

## Related Guidelines

- See `guidelines/code/validation.md` for general build and verification rules.
- See `techniques/ue-custom-graph-editor.md` for the step-by-step graph editor setup procedure.
