# Graph Data Ownership

## Core Problem

Custom graph editors that maintain a **separate runtime data model** alongside UE's
`UEdGraph` pin layer must decide: which layer owns each type of data?

Getting this wrong leads to fragile manual sync — every editing operation must
explicitly synchronize both layers, and missing a single sync point causes
silent data desync bugs.

## Data Ownership by Type

| Data Type | Source of Truth | Derived Layer | Why |
|-----------|----------------|---------------|-----|
| **Node properties** (speaker, text, etc.) | Runtime object (`UObject`) | Graph node displays it | Details panel edits the runtime object directly |
| **Connection topology** (who connects to who) | Graph pins (`UEdGraphPin::LinkedTo`) | Runtime transitions (e.g. `OutTransitions[]`) | `SGraphEditor` directly modifies pin arrays on user drag — this is a framework constraint, not a design choice |
| **Edge properties** (conditions, priorities) | Graph-side edge node (e.g. TransitionNode) | Runtime transition struct carries them after compile | Edge properties belong where the edge is authored — the graph layer |
| **Node position** | Graph node (`NodePosX/Y`) | N/A (editor-only) | Only meaningful in editor |

## The SGraphEditor Constraint

`SGraphEditor` owns the pin connection lifecycle. When a user drags a wire:

1. UE framework calls `UEdGraphSchema::TryCreateConnection()` — pin arrays are
   modified **before** your code runs.
2. Your Schema override receives notification **after** the pin change.
3. You **cannot prevent** the pin modification or redirect it to your data layer first.

This means: for connection data, the graph pin layer is always modified first.
Any runtime connection data must be **derived from** graph pins, not the other way around.

## Recommended Pattern: Compile (Full Flush)

Instead of incremental sync (updating runtime data in every Schema method), use a
single compile function that rebuilds all runtime connection data from the graph:

```
User drags wire
  -> SGraphEditor modifies pins
  -> NotifyGraphChanged fires
  -> CompileTransitions() walks all pins, rebuilds all OutTransitions from scratch
```

**Advantages:**
- Sync logic exists in ONE place (the compile function)
- Impossible to miss a sync point — every graph change triggers full rebuild
- No incremental sync code needed in TryCreateConnection, BreakPinLinks,
  BreakSinglePinLink, DeleteSelectedNodes, OnPinConnectionDoubleCicked, etc.

**Prerequisites:**
- All edge properties (conditions, priorities) must live on the graph-side edge
  node, not on the runtime transition struct. Otherwise compile has no source
  for these values.
- The compile function must be idempotent: running it twice produces the same result.

**When to compile:**
- After every graph change (via `NotifyGraphChanged` callback) — simplest, works
  well for small graphs (tens of nodes).
- On save / PIE start — deferred, better for large graphs but allows temporary
  desync during editing.

## Anti-Patterns

### Incremental Sync in Every Operation

```cpp
// BAD: every operation manually syncs runtime data
void Schema::TryCreateConnection(...) {
    Super::TryCreateConnection(...);
    // manual sync: add to OutTransitions...
}
void Schema::BreakPinLinks(...) {
    // manual sync: remove from OutTransitions...
    Super::BreakPinLinks(...);
}
void Editor::DeleteSelectedNodes() {
    // manual sync: remove from OutTransitions...
    Pin->BreakAllPinLinks(true);  // oops, this bypasses Schema!
}
```

This pattern requires every code path to remember to sync. Missing one (like
`Pin->BreakAllPinLinks` bypassing the Schema) creates silent desync.

### Storing Edge Properties on the Runtime Side Only

If edge properties (conditions, priorities) only exist on the runtime transition
struct, a compile (full rebuild) would lose them. Edge properties must be stored
on the graph-side edge node so compile can read them.

## Coexistence: Two Data Flows in One Editor

A custom graph editor typically has two data flow directions coexisting:

```
Node properties:  Runtime Object  -->  Graph Node displays it
                  (source)              (view)

Connections:      Graph Pins      -->  Runtime OutTransitions
                  (source)              (derived via compile)
```

These flows go in **opposite directions**. This is inherent to UE's graph
framework — node properties are edited via the Details panel (which writes to
the runtime object), while connections are edited via drag-and-drop (which writes
to graph pins).

Acknowledging this asymmetry — rather than trying to force a single data flow
direction — leads to a cleaner architecture.
