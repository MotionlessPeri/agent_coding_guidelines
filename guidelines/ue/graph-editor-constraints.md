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

## Cold Rebuild Over Live Coding

- After modifying plugin or C++ Graph Editor code, always use a cold rebuild
  (close editor → build → relaunch) instead of Live Coding.
- Live Coding frequently leaves stale widget caches, factory registrations, and
  slate state that produce behavior inconsistent with the actual code.
- Use Live Coding only for trivial, non-structural changes (string literals, log messages).

## Related Guidelines

- See `guidelines/code/validation.md` for general build and verification rules.
- See `techniques/ue-custom-graph-editor.md` for the step-by-step graph editor setup procedure.
