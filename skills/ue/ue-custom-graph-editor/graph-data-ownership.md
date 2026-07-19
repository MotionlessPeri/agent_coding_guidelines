# Graph Data Ownership（UE UEdGraph 编辑器执行面）

> Framework-agnostic 原则（按数据类型定 source-of-truth / 派生用 full-flush compile 不 incremental sync /
> 两条流可反方向）见 `guidelines/code/dual-layer-data-ownership.md`。本文是它在 **UE 自定义 `UEdGraph`
> 编辑器**（graph pin 层 + 独立 runtime 数据层）的执行面：UE 框架强加的约束 + 具体数据归属表 +
> compile 时机 + UE 反 pattern 代码。

## Core Problem

Custom graph editors that maintain a **separate runtime data model** alongside UE's
`UEdGraph` pin layer must decide: which layer owns each type of data? Getting this wrong
leads to fragile manual sync — missing a single sync point causes silent data desync.

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

**Advantages**（通用「single full-flush > incremental sync」的好处见 general 条）：UE 里的具体收益是
`TryCreateConnection` / `BreakPinLinks` / `BreakSinglePinLink` / `DeleteSelectedNodes` /
`OnPinConnectionDoubleCicked` 等 Schema 方法**全都不需要写** incremental sync 代码。

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

These flows go in **opposite directions** — node properties are edited via the Details
panel (writes to the runtime object), connections via drag-and-drop (writes to graph pins).
This asymmetry is inherent to UE's graph framework; acknowledge it rather than forcing a
single direction（通用「两条流可反方向」条同理）。
