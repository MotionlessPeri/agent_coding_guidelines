---
name: ue-custom-graph-editor
description: Use when building a custom node-graph editor inside a UE plugin (a Blueprint / Material / Behavior-Tree-style UEdGraph editor with your own nodes, schema, SGraphNode widgets, asset editor toolkit), or deciding how a custom graph editor runtime data model relates to the UEdGraph pin layer. Bundles the 7-step build procedure (runtime data model to asset to UEdGraphNode to schema to SGraphNode + factory to editor toolkit to asset actions, each with its pitfall + verification checkpoint) and the graph data-ownership rules (which layer owns node properties vs connection topology vs edge properties, the SGraphEditor pin-first constraint, compile-full-flush over incremental sync). Hard per-API constraints (NodeGuid init, pin SetOwner, RF_Transactional, undo refresh, copy-paste DuplicateObject) stay in the always-loaded guidelines/ue/graph-editor-constraints.md. Skip for non-UE work or UE work using the built-in Blueprint / Animation graphs rather than a new custom graph editor.
---

# UE 自定义 Graph Editor

从零建一个 UE 自定义 node-graph 编辑器（类似 Blueprint / Material / Behavior Tree 编辑器）时的
两块内容。**Ultra-niche**——只在真的要做一个**新的** `UEdGraph` 编辑器时命中（用内置 BP / Anim 图不需要）。

| 内容 | 覆盖 | 文档 |
|---|---|---|
| **Build 流程** | 7 步 step-by-step：runtime data model → asset class → `UEdGraphNode` 子类 → `UEdGraphSchema` → `SGraphNode` + factory 注册 → asset editor toolkit → asset type actions。每步带**关键坑** + **验证 checkpoint**，Prerequisites 强调先读最相近的 engine reference impl | [`ue-custom-graph-editor.md`](ue-custom-graph-editor.md) |
| **数据归属** | graph pin 层 + 独立 runtime 数据层时，哪层拥有哪类数据（node 属性 / connection 拓扑 / edge 属性）；`SGraphEditor` pin-first 硬约束；compile full-flush > incremental sync；UE 反 pattern 代码 | [`graph-data-ownership.md`](graph-data-ownership.md) |

**硬 per-API 约束**（NodeGuid 初始化 / pin `SetOwner` 一次 / Custom SGraphNode factory 注册 / `RF_Transactional` /
undo refresh / copy-paste `DuplicateObject` / reroute 节点 4 件套等）**不在本 skill**——它们是常碰的 broad
契约，常驻在 `guidelines/ue/graph-editor-constraints.md`，本 skill 的两份文档处处引用它。

## When This Fires

- 第一次在 UE plugin 里做一个自定义 asset 的 node-graph 编辑器（自己的节点 / schema / SGraphNode / toolkit）
- 设计「graph pin 层 ↔ 独立 runtime 数据模型」的数据归属 + 同步策略
- 撞到 custom graph editor 的 subtle bug（连线拖不动 / undo 崩 / 节点数据 desync / reroute 显示错）

## How to Apply

1. **动手前**先按 `ue-custom-graph-editor.md` Prerequisites + skill `ue-reference-engine-source` 找最相近的
   engine reference impl（Animation State Machine / Material Editor / Behavior Tree）读一遍——UE graph 框架
   大量隐式契约只在 existing impl 里可见。
2. **按 7 步推进**，每步翻 `graph-editor-constraints.md`（常驻）对应章节 + 过该步的验证 checkpoint。
3. **数据模型**用 `graph-data-ownership.md`：连接拓扑一律 graph pins → runtime 派生（compile full-flush），
   别在每个 Schema 方法里增量 sync。

## Related

- `guidelines/ue/graph-editor-constraints.md` —— 常驻的硬 per-API 约束集（本 skill 两份文档的引用底座）
- `guidelines/code/dual-layer-data-ownership.md` —— `graph-data-ownership.md` 的 framework-agnostic 上位原则（双层数据模型：按类型定 SoT + 派生别 sync，泛化到 Maya / GUI / ORM）
- skill `ue-reference-engine-source` —— build 流程 Prerequisites 的展开（按子系统找 engine reference）
- skill `ue-module-architecture` —— 编辑器操作分层（Runtime Ops / Editor Actions / UI）+ undo support
